from __future__ import print_function, division, absolute_import

import tempfile
import os
import shutil
import errno
import operator
import multiprocessing
import logging
import csv



from . import remote_smac
from .utils.multiprocessing_wrapper import MyPool


class SMAC_optimizer(object):
   
    # collects smac specific data that goes into the scenario file
    def __init__(self, deterministic = True, t_limit_total_s=None, mem_limit_smac_mb=None, working_directory = None, persistent_files=False, debug = False):
        
        self.__logger = multiprocessing.log_to_stderr()
        if debug:
            self.__logger.setLevel(debug)
        else:
            self.__logger.setLevel(logging.WARNING)
        
        
        self.__t_limit_total_s = 0 if t_limit_total_s is None else int(t_limit_total_s)
        self.__mem_limit_smac_mb = None if (mem_limit_smac_mb is None) else int(mem_limit_smac_mb)
            
        self.__persistent_files = persistent_files
        
        
        # some basic consistency checks

        if (self.__t_limit_total_s < 0):
            raise ValueError('The total time limit cannot be nagative!')
        if (( self.__mem_limit_smac_mb is not None) and (self.__mem_limit_smac_mb <= 0)):
            raise ValueError('SMAC\'s memory limit has to be either None (no limit) or positive!')

        
        # create a temporary directory if none is specified
        if working_directory is None:
            self.working_directory = tempfile.mkdtemp()
        else:
            self.working_directory = working_directory
        
        self.__logger.debug('Writing output into: %s'%self.working_directory)
        
        # make some subdirs for output and smac internals
        self.__exec_dir = os.path.join(self.working_directory, 'exec')
        self.__out_dir  = os.path.join(self.working_directory, 'out' )

        for directory in [self.working_directory, self.__exec_dir, self.__out_dir]:
            try:
                os.makedirs(directory)
            except OSError as exception:
                if exception.errno != errno.EEXIST:
                    raise
        
                
        # Set some of smac options
        # Most fields contain the standard values (as of SMAC 2.08.00).
        # All options from the smac manual can be accessed by
        # adding an entry to the dictionary with the appropriate name.
        # Some options will however have, at best, no effect, setting
        # others may even brake the communication.
        self.smac_options = {
            'algo-exec': 'echo 0',
            'run-obj': 'QUALITY',
            'algo-deterministic': deterministic,
            'validation': False,
            'cutoff_time': 3600,
            'intensification-percentage': 0.5,
            'numPCA': 7,
            'rf-full-tree-bootstrap': False,
            'rf-ignore-conditionality':False,
            'rf-num-trees': 10,
            'skip-features': True,
            'pcs-file': os.path.join(self.working_directory,'parameters.pcs'),
            'instances': os.path.join(self.working_directory ,'instances.dat'),
            'algo-exec-dir': self.working_directory,
            'output-dir': self.__out_dir,
            'console-log-level': 'OFF',
            'abort-on-first-run-crash': False,
            'overall_obj': 'MEAN',
            'scenario_fn': 'scenario.dat', # NOT A SMAC OPTION, but allows to
                                          # change the standard name (used for 
                                          # in SpySMAC)
            'java_executable': 'java'
            }
        if debug:
            self.smac_options['console-log-level']='INFO'


    # after SMAC finishes, some cleanup has to be done depending on persistent_files
    def __del__(self):
        if not self.__persistent_files:
            shutil.rmtree(self.working_directory)
    
    
    # find the minimum given a function handle and a specification of its parameters and optional
    # conditionals and forbidden clauses
    def minimize(self, func, max_evaluations, parameter_dict, 
            conditional_clauses = [], forbidden_clauses=[], 
            num_train_instances = None, num_test_instances = None,
            seed = None,  num_procs = 1, num_runs = 1,
            mem_limit_function_mb=None, t_limit_function_s= None):
        
        
        num_train_instances = None if (num_train_instances is None) else int(num_train_instances)
        
        if (num_train_instances is not None):
            if (num_train_instances < 1):
                raise ValueError('The number of training instances must be positive!')

        num_procs = int(num_procs)
        pcs_string, parser_dict = remote_smac.process_parameter_definitions(parameter_dict)

        # adjust the seed variable
        if seed is None:
            seed = list(range(num_runs))
        elif isinstance(seed, int) and num_runs == 1:
            seed = [seed]
        elif isinstance(seed, int) and num_runs > 1:
            seed = list(range(seed, seed+num_runs))
        elif isinstance(seed, list) or isinstance(seed, tuple):
            if len(seed) != num_runs:
                raise ValueError("You have to specify a seed for every instance!")
        else:
            raise ValueError("The seed variable could not be properly processed!")
        
        
        self.smac_options['runcount-limit'] = max_evaluations
        if t_limit_function_s is not None:
            self.smac_options['cutoff_time'] = t_limit_function_s
        
        
        # create and fill the pcs file
        with open(self.smac_options['pcs-file'], 'w') as fh:
            fh.write("\n".join(pcs_string + conditional_clauses + forbidden_clauses))
        
        #create and fill the instance files
        tmp_num_instances = 1 if num_train_instances is None else num_train_instances
        with open(self.smac_options['instances'], 'w') as fh:
            for i in range(tmp_num_instances):
                fh.write("id_%i\n"%i)
        
        if num_test_instances is not None:
            self.smac_options['validate-only-last-incumbent'] = True
            self.smac_options['validation'] = True
            self.smac_options['test-instances'] = os.path.join(self.working_directory, 'test_instances.dat')
            with open(self.smac_options['test-instances'],'w') as fh:
                for i in range(tmp_num_instances, tmp_num_instances + num_test_instances):
                    fh.write("id_%i\n"%i)

        # create and fill the scenario file
        scenario_fn = os.path.join(self.working_directory,self.smac_options.pop('scenario_fn'))
        java_executable = self.smac_options.pop('java_executable');
        
        scenario_options = {'algo', 'algo-exec', 'algoExec',
                            'algo-exec-dir', 'exec-dir', 'execDir','execdir',
                            'deterministic', 'algo-deterministic',
                            'paramfile', 'paramFile', 'pcs-file', 'param-file',
                            'run-obj', 'run-objective', 'runObj', 'run_obj',
                            'intra-obj', 'intra-instance-obj', 'overall-obj', 'intraInstanceObj', 'overallObj', 'overall_obj', 'intra_instance_obj',
                            'algo-cutoff-time', 'target-run-cputime-limit', 'target_run_cputime_limit', 'cutoff-time', 'cutoffTime', 'cutoff_time',    
                            'cputime-limit', 'cputime_limit', 'tunertime-limit', 'tuner-timeout', 'tunerTimeout',
                            'wallclock-limit', 'wallclock_limit', 'runtime-limit', 'runtimeLimit', 'wallClockLimit',
                            'output-dir', 'outputDirectory', 'outdir',
                            'instances', 'instance-file', 'instance-dir', 'instanceFile', 'i', 'instance_file', 'instance_seed_file',
                            'test-instances', 'test-instance-file', 'test-instance-dir', 'testInstanceFile', 'test_instance_file', 'test_instance_seed_file',                            
                            'feature-file', 'instanceFeatureFile', 'feature_file'
                            }
        
        additional_options_fn =scenario_fn[:-4]+'.advanced' 
        with open(scenario_fn,'w') as fh, open(additional_options_fn, 'w') as fg:
            for name, value in list(self.smac_options.items()):
                if name in scenario_options:
                    fh.write('%s %s\n'%(name, value))
                else:
                    fg.write('%s %s\n'%(name,value))
        
        # check that all files are actually present, so SMAC has everything to start
        assert all(map(os.path.exists, [additional_options_fn, scenario_fn, self.smac_options['pcs-file'], self.smac_options['instances']])), "Something went wrong creating files for SMAC! Try to specify a \'working_directory\' and set \'persistent_files=True\'."

        # create a pool of workers and make'em work
        pool = MyPool(num_procs)
        argument_lists = [[scenario_fn, additional_options_fn, s, func, parser_dict, self.__mem_limit_smac_mb, remote_smac.smac_classpath(),  num_train_instances, mem_limit_function_mb, t_limit_function_s, self.smac_options['algo-deterministic'], java_executable] for s in seed]
        
        pool.map(remote_smac.remote_smac_function, argument_lists)
        
        pool.close()
        pool.join()
        
        # find overall incumbent and return it
        
        scenario_dir = os.path.join(self.__out_dir,'.'.join(scenario_fn.split('/')[-1].split('.')[:-1]))
        
        run_incumbents = []
        
        for s in seed:
            with open( os.path.join(scenario_dir, 'traj-run-%i.txt'%s)) as csv_fh:
                try:
                    csv_r = csv.reader(csv_fh)
                    for row in csv_r:
                        incumbent = row
                    run_incumbents.append((float(incumbent[1]), [s.strip(" ") for s in incumbent[5:]]))
                except:
                    pass
        
        run_incumbents.sort(key = operator.itemgetter(0))            
        
        conf_dict = {}
        for c in run_incumbents[0][1]:
            c = c.split('=')
            conf_dict[c[0]] = parser_dict[c[0]](c[1].strip("'"))
        return( run_incumbents[0][0], conf_dict )
