from __future__ import print_function, absolute_import, unicode_literals

import sys
import os
import traceback
import socket
import subprocess
import resource
from pkg_resources import resource_filename
from math import ceil

import logging
import multiprocessing

import time

import pysmac.utils.limit_resources


SMAC_VERSION = "smac-v2.08.00-master-731"

try:
    str=unicode #Python 2 backward compatibility
except NameError:
    pass        #Python 3 case


# takes a name and a tuple defining one parameter, registers that with the parser
# and returns the corresponding string for the SMAC pcs file and the type of the
# variable for later casting
def process_single_parameter_definition(name, specification):
    # if this is the first parameter, set up the argument parser for SMACs output
    
    string = '%s '%name

    assert isinstance(specification, (list,tuple)), "The specification \"%s\" is not valid"%(specification,)
    assert len(specification)>1, "The specification \"%s\" is too short"%(specification,)
    dtype=str

    # numerical values
    if isinstance(specification[0], (list, tuple)):
        
        dtype=float
        ao = set(specification[2:])
        tmp_string=''
        
        if 'int' in ao:
            tmp_string +='i'
            ao.remove('int')
            dtype=int
        if 'log' in ao:
            tmp_string +='l'
            ao.remove('log')
        assert len(ao) == 0, "unknown option(s) %s"%(list(ao), )

        string += '[ %s, %s] [%s] '%(str(dtype(specification[0][0])), str(dtype(specification[0][1])), str(dtype(specification[1]))) + tmp_string
    #categorical values
    elif isinstance(specification[0], set):
        string += '{'+ ','.join(map(str,specification[0])) +'} [%s]'%specification[1]
    else:
        raise ValueError("Sorry, I don't understand the parameter specification: %s\n"%(specification,))

    return string, dtype


# takes the users parameter definition and converts into lines for the pcs file
# and also creates a dictionary for parsing smacs output
def process_parameter_definitions(parameter_dict):
    pcs_strings = []
    parser_dict={}
    
    for k,v in parameter_dict.items():
        line, dtype = process_single_parameter_definition(k,v)
        parser_dict[k] = dtype
        pcs_strings.append(line)
        
    return (pcs_strings, parser_dict)



# function that gathers all information to build the java class path
def smac_classpath():
    logger = multiprocessing.get_logger()
    
    smac_folder = resource_filename("pysmac", 'smac/%s' % SMAC_VERSION)
    # hack for development :)
    # smac_folder = './%s/'%SMAC_VERSION
    
    smac_conf_folder = os.path.join(smac_folder, "conf")
    smac_patches_folder = os.path.join(smac_folder, "patches")
    smac_lib_folder = os.path.join(smac_folder, "lib")


    classpath = [fname for fname in os.listdir(smac_lib_folder) if fname.endswith(".jar")]
    classpath = [os.path.join(smac_lib_folder, fname) for fname in classpath]
    classpath = [os.path.abspath(fname) for fname in classpath]
    classpath.append(os.path.abspath(smac_conf_folder))
    classpath.append(os.path.abspath(smac_patches_folder))

    # Windows compability
    classpath = ';'.join(classpath) if os.name == 'nt' else ':'.join(classpath)

    logger.debug("SMAC classpath: %s", classpath)

    return classpath





class remote_smac(object):
    udp_timeout=1
    
    # Starts SMAC in IPC mode. SMAC will wait for udp messages to be sent.
    def __init__(self, scenario_fn, additional_options_fn, seed, class_path, memory_limit, parser_dict):
        self.__parser = parser_dict
        self.__subprocess = None
        self.__logger = multiprocessing.get_logger()
        
        # establish a socket
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__sock.settimeout(3)
        self.__sock.bind(('', 0))
        self.__sock.listen(1)
        
        self.__port = self.__sock.getsockname()[1]
        self.__logger.debug('picked port %i'%self.__port)

        # build the java command
        cmds  = ["java"]
        if memory_limit is not None:
            cmds += ["-Xmx%im"%memory_limit]
        cmds +=    ["-cp",
                class_path,
                "ca.ubc.cs.beta.smac.executors.SMACExecutor",
                "--scenario-file", scenario_fn,
                "--tae", "IPC",
                "--ipc-mechanism", "TCP",
                "--ipc-remote-port", str(self.__port),
                "--seed", str(seed)
                ]
        
        with open(additional_options_fn, 'r') as fh:
            for line in fh:
                name, value = line.strip().split(' ')
                cmds += ['--%s'%name, '%s'%value]
        
        self.__logger.debug("SMAC command: %s"%(' '.join(cmds)))
        
        self.__logger.debug("Starting SMAC in ICP mode")
        
        # connect the output to the logger if the appropriate level has been set
        if self.__logger.level < logging.WARNING:
            self.__subprocess = subprocess.Popen(cmds, stdout =sys.stdout, stderr = sys.stderr)
        else:
            with open(os.devnull, "w") as fnull:
                self.__subprocess = subprocess.Popen(cmds, stdout = fnull, stderr = fnull)

    def __del__(self):
        # shut the subprocess down on 'destruction'
        if not (self.__subprocess is None):
            self.__subprocess.poll()
            if self.__subprocess.returncode == None:
                self.__subprocess.kill()
                self.__logger.debug('SMAC had to be terminated')
            else:    
                self.__logger.debug('SMAC terminated with returncode %i', self.__subprocess.returncode)


    def next_configuration(self):
        
        while True:
            try:
                self.__logger.debug('trying to retrieve the next configuration from SMAC')
                self.__sock.settimeout(self.udp_timeout)
                self.__conn, addr = self.__sock.accept()
                fconn = self.__conn.makefile('r') 
                config_str = fconn.readline()
                break
            except socket.timeout:
                # if smac already terminated, there is nothing else to do
                if self.__subprocess.poll() is not None:
                    self.__logger.debug("SMAC subprocess is no longer alive!")
                    return None    
                #otherwise there is funny business going on!
                else:
                    self.__logger.debug("SMAC has not responded yet, but is still alive. Will keep waiting!")

        self.__logger.debug("SMAC message: %s"%config_str)
        
        los = config_str.replace('\'','').split() # name is shorthand for 'list of strings'
        config_dict={}

                
        config_dict['instance']      = int(los[0][3:])
        config_dict['instance_info'] = str(los[1])
        config_dict['cutoff_time']   = float(los[2])
        config_dict['cutoff_length'] = float(los[3])
        config_dict['seed']          = int(los[4])

        
        for i in range(5, len(los), 2):
            config_dict[ los[i][1:] ] = self.__parser[ los[i][1:] ]( los[i+1])
        
        self.__logger.debug("Our interpretation: %s"%config_dict)
        return (config_dict)
    
    def report_result(self, value, runtime, status = b'CRASHED'):
        tmp ={'status': status, 'runtime': runtime}
        
        # value is only None, if the function call was unsuccessful
        if value is None:
            tmp['value'] = 0
        # for fancy stuff, the function can return a dict with 'status',
        # 'runtime',  and 'value' keys (does not have to provide all, though)
        elif isinstance(value, dict):
            tmp.update(value)
        # in all other cases, it should be a float
        else:
            tmp['value'] = value
        
        # for propper printing, we have to convert the status into unicode
        tmp['status'] = tmp['status'].decode()
        s = u'Result for ParamILS: {0[status]}, {0[runtime]}, 0, {0[value]}, 0\
            '.format(tmp)
        print(s)
        self.__conn.sendall(s.encode())
        self.__conn.close();



def remote_smac_function(only_arg):
    try:
    
        scenario_file, additional_options_fn, seed, function, parser_dict,\
          memory_limit_smac_mb, class_path, num_instances, mem_limit_function,\
          t_limit_function, deterministic = only_arg
    
        logger = multiprocessing.get_logger()
    
        smac = remote_smac(scenario_file, additional_options_fn, seed, 
                               class_path, memory_limit_smac_mb,parser_dict)
    
        logger.debug('Started SMAC subprocess')
    
        num_iterations = 0
    
        while True:
            config_dict = smac.next_configuration()

            # method next_configuration checks whether smac is still alive
            # if it is None, it means that SMAC has finished (for whatever reason)
            if config_dict is None:
                break
            
            # delete the unused variables from the dict
            if num_instances is None:
                del config_dict['instance']
            
            del config_dict['instance_info']
            del config_dict['cutoff_length']
            if deterministic:
                del config_dict['seed']
        
            current_t_limit = int(ceil(config_dict.pop('cutoff_time')))

            # execute the function and measure the time it takes to evaluate
            wrapped_function = pysmac.utils.limit_resources.enforce_limits(
                mem_in_mb=mem_limit_function,
                cpu_time_in_s=current_t_limit,
                wall_time_in_s=10*current_t_limit,
                grace_period_in_s = 1)(function)

            # workaround for the 'Resource temporarily not available' error on
            # the BaWue cluster if to many processes were spawned in a short
            # period. It now waits a second and tries again for 8 times.
            num_try = 1
            while num_try <= 8:
                try:
                    start = time.time()
                    res = wrapped_function(**config_dict)
                    wall_time = time.time()-start
                    cpu_time = resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime
                    break
                except OSError as e:
                    if e.errno == 11:
                        logger.warning('Resource temporarily not available. Trail {} of 8'.format(num_try))
                        time.sleep(1)
                    else:
                        raise
                except:
                    raise
                finally:
                    num_try += 1
            if num_try == 9:
                logger.warning('Configuration {} crashed 8 times, giving up on it.'.format(config_dict))
                res = None
            
            if res is not None:
                logger.debug('iteration %i:function value %s, computed in %s seconds'%(num_iterations, str(res), str(res['runtime'])))
            else:
                logger.debug('iteration %i: did not return in time, so it probably timed out'%(num_iterations))


            # try to infere the status of the function call:
            # if res['status'] exsists, it will be used in 'report_result'
            # if there was no return value, it has either crashed or timed out
            # for simple function, we just use 'SAT'
            status = b'CRASHED' if res is None else b'SAT'
            try:
                # check if it recorded some runtime by itself and use that
                if res['runtime'] > current_t_limit - 2e-2: # mini slack to account for limited precision of cputime measurement
                    status=b'TIMEOUT'
            except (AttributeError, TypeError, KeyError):
                # if not, we have to use our own time measurements here
                if (res is None) and ((cpu_time > current_t_limit - 2e-2) or
                                            (wall_time >= 10*current_t_limit)):
                    status=b'TIMEOUT'
            except:
                # reraise in case something else went wrong
                raise

            smac.report_result(res, cpu_time, status)
            num_iterations += 1
    except:
        traceback.print_exc() # to see the traceback of subprocesses
