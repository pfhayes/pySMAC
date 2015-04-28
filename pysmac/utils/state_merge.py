import sys

sys.path.append('../../')

import os
import glob
import operator
import errno
import filecmp
import shutil
import numpy


import pysmac.utils.smac_output_readers as readers



def read_sate_run_folder(directory, rar_fn = "runs_and_results-it*.csv",inst_fn = "instances.txt" , feat_fn = "instance-features.txt" , ps_fn = "paramstrings-it*.txt"):    
    print("reading {}".format(directory))
    configs = readers.read_paramstrings_file(glob.glob(os.path.join(directory,ps_fn))[0])
    instance_names = readers.read_instances_file(glob.glob(os.path.join(directory,inst_fn))[0])
    runs_and_results = readers.read_runs_and_results_file(glob.glob(os.path.join(directory, rar_fn))[0])
    full_feat_fn = glob.glob(os.path.join(directory,feat_fn))
    if len(full_feat_fn) == 1:      
        instance_features = readers.read_instance_features_file(full_feat_fn[0])
    else:
        print("No feature file")
        instance_features = None

    return (configs, instance_names, instance_features, runs_and_results)



def state_merge( state_run_directory_list, destination, drop_duplicates = False):

    configurations = {}
    instances = {}
    runs_and_results = {}
    ff_header= set()
    
    i_confs = 1;
    i_insts = 1;


    # make sure all pcs files are the same
    pcs_files = map(lambda d: os.path.join(d,'param.pcs'), state_run_directory_list)
    if not all(map(lambda fn: filecmp.cmp(fn, pcs_files[0]), pcs_files[1:])):
        raise RuntimeError("The pcs files of the different runs are not identical!")

    scenario_files = map(lambda d: os.path.join(d,'scenario.txt'), state_run_directory_list)
    if not all(map(lambda fn: filecmp.cmp(fn, scenario_files[0]), scenario_files[1:])):
        raise RuntimeError("The scenario files of the different runs are not identical!")



    for directory in state_run_directory_list:
        #try:
        confs, inst_names, tmp , rars = read_sate_run_folder(directory)

        
        (header_feats, inst_feats) = tmp if tmp is not None else (None,None)

        
        #except:
        #    print("Something went wrong while reading {}. Skipping it.".format(directory))
        #    continue
        
        # confs is a list of dicts, but dicts are not hashable, so they are
        # converted into a tuple of (key, value) pairs and then sorted
        confs = map(lambda d: tuple(sorted(d.items())), confs)        
        
        # merge the configurations
        for conf in confs:
            if not conf in configurations:
                configurations[conf] = {'index': i_confs}
                i_confs += 1
        # merge the instances
        for i in range(len(inst_names)):
            if not inst_names[i][0] in instances:
                instances[inst_names[i][0]] = {'index': i_insts}
                instances[inst_names[i][0]]['features'] =  inst_feats[inst_names[i][0]] if inst_feats is not None else None
                instances[inst_names[i][0]]['additional info'] = ' '.join(inst_names[i][1:]) if len(inst_names[i]) > 1 else None
                i_insts += 1
            else:
                if (inst_feats is None):
                    if not (instances[inst_names[i][0]]['features'] is None):
                        raise ValueError("The data contains the same instance name ({}) twice, but once with and without features!".format(inst_names[i]))
                elif not instances[inst_names[i][0]]['features'] == inst_feats[inst_names[i][0]]:
                    raise ValueError("The data contains the same instance name ({}) twice, but with different features!".format(inst_names[i]))
                pass
        
        # store the feature file header:
        ff_header.add(header_feats)
        
        if len(ff_header) != 1:
            raise RuntimeError("Feature Files not consistent across runs!\n{}".format(header_feats))
        
        
        if len(rars.shape) == 1:
            rars = numpy.array([rars])
        for run in rars:
            # get the local configuration and instance id
            lcid, liid = int(run[0])-1, int(run[1])-1

            # translate them into the global ones
            gcid = configurations[confs[lcid]]['index']
            giid = instances[inst_names[liid][0]]['index']

            # check for duplicates and skip if necessary
            if (gcid, giid) in runs_and_results:
                if drop_duplicates:
                    #print('dropped duplicate: configuration {} on instace {}'.format(gcid, giid))
                    continue
                else: runs_and_results[(gcid, giid)].append(run[3:])
            else:
                runs_and_results[(gcid, giid)] = [run[2:]]

    # create output directory
    try:
        os.makedirs(destination)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass
        else:
            raise
        
    # create all files, overwriting exisating ones
    shutil.copy(pcs_files[0], destination)
    shutil.copy(scenario_files[0], destination)
        

    with open(os.path.join(destination, 'instances.txt'),'w') as fh:
        sorted_instances = []
        for name in instances:
            if instances[name]['additional info'] is not None:
                sorted_instances.append( (instances[name]['index'], name + ' ' + instances[name]['additional info']) )
            else:
                sorted_instances.append( (instances[name]['index'], name) )
        
        sorted_instances.sort()
        fh.write('\n'.join(map(operator.itemgetter(1), sorted_instances)))

    with open(os.path.join(destination, 'runs_and_results-it0.csv'),'w') as fh:
        cumulative_runtime = 0.0
        
        fh.write("Run Number,Run History Configuration ID,Instance ID,"
                 "Response Value (y),Censored?,Cutoff Time Used,"
                 "Seed,Runtime,Run Length,"
                 "Run Result Code,Run Quality,SMAC Iteration,"
                 "SMAC Cumulative Runtime,Run Result,"
                 "Additional Algorithm Run Data,Wall Clock Time,\n")
        run_i = 1
        for ((conf,inst),res) in runs_and_results.items():
            for r in res:
                fh.write('{},{},{},'.format(run_i, conf, inst))
                fh.write('{},{},{},'.format(r[0], int(r[1]), r[2]))
                fh.write('{},{},{},'.format(int(r[3]), r[4], r[5]))
                fh.write('{},{},{},'.format(int(r[6]), r[7], 0))
                
                cumulative_runtime += r[4]
                if r[10] == 2:
                    tmp = 'SAT'       
                if r[10] == 1:
                    tmp = 'UNSAT'
                if r[10] == 0:
                    tmp = 'TIMEOUT'
                if r[10] == -1:
                    tmp = 'CRASHED'
                
                fh.write('{},{},,{},'.format(cumulative_runtime,tmp, r[11]))
                fh.write('\n')
                run_i += 1

    with open(os.path.join(destination, 'paramstrings-it0.txt'),'w') as fh:
        sorted_confs = [(configurations[k]['index'],k) for k in configurations.keys()]
        sorted_confs.sort()
        for conf in sorted_confs:
            fh.write("{}: ".format(conf[0]))
            fh.write(", ".join(["{}='{}'".format(p[0],p[1]) for p in conf[1]]))
            fh.write('\n')

    if set(map(operator.itemgetter('features'), instances.values())) != set([None]):
        with open(os.path.join(destination, 'instance-features.txt'),'w') as fh:
            fh.write(ff_header.pop())
            sorted_features = [(instances[inst]['index'], inst + ',' + instances[inst]['features']) for inst in instances]
            sorted_features.sort()
            fh.write('\n'.join([ t[1] for t in sorted_features]))

    return(configurations, instances, runs_and_results, sorted_instances, sorted_confs, inst_feats)