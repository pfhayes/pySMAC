

import pysmac


import sklearn.ensemble
import sklearn.neighbors
import sklearn.datasets
import sklearn.cross_validation




# We use the same data as the earlier sklearn examples. We also use the static
# train-test split for convinience
X,Y = sklearn.datasets.make_classification(1000, 20)
X_train, X_test, Y_train, Y_test = sklearn.cross_validation.train_test_split(X,Y, test_size=0.33, random_state=1)





# Now SMAC can choose between to different models at each evaluation. To make the
# search most efficient, it is important to tell SMAC that some parameters are
# associated with certain classifiers
def classifier(classifier, # which classifier to use, this is a mandatory argument and will always be given
				rf_n_estimators = None, rf_criterion = None, # these two lines are the parameters for the random forest
				rf_max_features = None, rf_max_depth = None, # they have to be optional as SMAC will not always assign values
				knn_n_neighbors=None, knn_weights=None):	# the same is true for the k-nearest-neighbor parameter
	
	if classifier == 'random_forest':
		predictor = sklearn.ensemble.RandomForestClassifier(rf_n_estimators, rf_criterion, rf_max_features, rf_max_depth)
	elif classifier == 'k_nearest_neighbors':
		predictor = sklearn.neighbors.KNeighborsClassifier(knn_n_neighbors, knn_weights)

	predictor.fit(X_train, Y_train)
	return -predictor.score(X_test, Y_test)




# defining all the parameters with respective defaults.
parameter_definition=dict(\
		rf_max_depth = ( [1,10], 4, 'int'),
		rf_max_features=( [1, 20],  10, 'int'),				
		rf_n_estimators=( [1, 100],  10, 'int', 'log'),			
		rf_criterion =( {'gini', 'entropy'}, 'entropy'),
		knn_n_neighbors = ([1,100], 10, 'log', 'int'),
		knn_weights = ( {'uniform', 'distance'}, 'uniform'),
		classifier = ({'random_forest', 'k_nearest_neighbors'}, 'random_forest'),
		)


# here we define the dependencies between the parameters. the notation is
# 	<child> | <parent> in { <parent value>, ... }
# and means that the child parameter is only active if the parent parameter takes
# one of the value in the listed set. The notation follows the SMAC manual one to one.
# note there is no checking for correctness beyond what SMAC does. I.e., when you have
# a typo in here, you don't get any output, unless you set  debug = True below!
conditionals = [	'rf_max_depth | classifier in {random_forest}',
					'rf_max_features | classifier in {random_forest}',
					'rf_n_estimators | classifier in {random_forest}',
					'rf_criterion | classifier in {random_forest}',
					'knn_n_neighbors | classifier in {k_nearest_neighbors}',
					'knn_weights | classifier in {k_nearest_neighbors}',
					]



# Same creation of the SMAC_optimizer object
opt = pysmac.SMAC_optimizer( working_directory = '/tmp/pysmac_test/',# the folder where SMAC generates output
							 persistent_files=False,					 # whether the output will persist beyond the python object's lifetime
							 debug = False,							 # if something goes wrong, enable this for diagnostic output
							)


# first we try the sklearn default, so we can see if SMAC can improve the performance

predictor = sklearn.ensemble.RandomForestClassifier()
predictor.fit(X_train, Y_train)
print('The default accuracy of the random forest is %f'%predictor.score(X_test, Y_test))

predictor = sklearn.neighbors.KNeighborsClassifier()
predictor.fit(X_train, Y_train)
print('The default accuracy of k-nearest-neighbors is %f'%predictor.score(X_test, Y_test))


import time
time.sleep(2)

# The minimize method also has optional arguments
value, parameters = opt.minimize(classifier,
					500 , parameter_definition,
					conditional_clauses = conditionals,
					num_runs = 2,					# number of independent SMAC runs
					seed = 0,						# the random seed used. can be an int or a list of ints of length num_runs
					num_procs = 2,					# pySMAC can harness multicore architecture. Specify the number of processes to use here.
					)
	
print('The highest accuracy found: %f'%(-value))
print('Parameter setting %s'%parameters)
