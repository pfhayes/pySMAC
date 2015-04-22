import sys

sys.path.append('../../')

import os
import glob


import pysmac.utils.smac_output_readers as readers



def read_sate_run_folder(directory, rar_fn = "runs_and_results-it*.csv",inst_fn = "instances.txt" , feat_fn = "instance-features.txt" , ps_fn = "paramstrings-it*.txt"):    
    
    configs = readers.read_paramstrings_file(glob.glob(os.path.join(directory,ps_fn))[0])
    instance_names = readers.read_instances_file(glob.glob(os.path.join(directory,inst_fn))[0])
    runs_and_results = readers.read_runs_and_results_file(glob.glob(os.path.join(directory, rar_fn))[0])
    full_feat_fn = glob.glob(os.path.join(directory,feat_fn))
    
    if len(full_feat_fn) > 0:
        instance_features = readers.read_instance_features_file(full_feat_fn[0])
    else:
        instance_features = None
    
    return (configs, instance_names, instance_features, runs_and_results)



def state_merge( state_run_directory_list, drop_duplicates = False):

    configurations = {}
    instances = {}
    
    i_confs = 1;
    i_insts = 1;

    for directory in state_run_directory_list:
        confs, inst_names, inst_feats, rars = read_sate_run_folder(directory)

        for conf in confs:
            if conf is not in configurations:
                configurations[conf] = {'index': i_confs}
                i_confs += 1
        for i in len(inst_names):
            if inst_names[i] is not in instances:
                instances[inst_names[i]] = {'index': i_insts}
                if inst_feats is not None:
                    instances[inst_names[i]] = {'features': inst_feats[inst_names[i]]}
                i_insts += 1
            else:
                #TODO make sure it has the same features
                pass
        
                




test_list = ['/home/sfalkner/repositories/bitbucket/pysmac2/spysmac_on_minisat_mini/out/scenario/state-run0',
	'/home/sfalkner/repositories/bitbucket/pysmac2/spysmac_on_minisat_mini/out/scenario/state-run1']


test_list = glob.glob("/home/sfalkner/repositories/data/*")
state_merge(test_list)
