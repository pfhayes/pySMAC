import os
import glob
import six
import json
import functools
import re
import operator

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as pltcm
from matplotlib.widgets import CheckButtons

from . import remote_smac


# taken from 
# http://stackoverflow.com/questions/21708192/how-do-i-use-the-json-module-to-read-in-one-json-object-at-a-time/21709058#21709058
def json_parse(fileobj, decoder=json.JSONDecoder(), buffersize=2048):
	buffer = ''
	for chunk in iter(functools.partial(fileobj.read, buffersize), ''):
		buffer += chunk
		buffer = buffer.strip(' \n')
		while buffer:
			try:
				result, index = decoder.raw_decode(buffer)
				yield result
				buffer = buffer[index:]
			except ValueError:
				# Not enough data to decode, read more
				break



class interactive_plot(object):

	def __init__(self):
		
		try:
			import mpldatacursor
			self.datacursor = True
		except:
			self.datacursor = False
		
		self.fig, self.ax = plt.subplots()
		self.datasets = []
		self.dataset_ids = []

	def add_datacursor(self, **kwargs):
		
		if not self.datacursor:
			print("Please install mpldatacursor if you want to have advanced interactive capabilities.")
			return()
		
		dict1 = dict(
				bbox=dict(alpha=1),
				formatter = 'iteration {x:.0f}: {y}\n{label}'.format,
				hover=False,
				display='multiple',
				draggable=True,
				horizontalalignment='center',
				hide_button = 3)
		
		dict1.update(kwargs)
		mpldatacursor.datacursor(**dict1)

	def scatter(self, run_id, xs, ys, labels= None, color='blue'):
		
		if labels is not None:
			self.datasets.append( [self.ax.scatter(x,y, label = l, color = color) for (x,y,l) in zip(xs, ys, labels)])
		else:
			self.datasets.append( [self.ax.scatter(xs,ys, color = color)])

		self.dataset_ids.append(run_id)

	def plot(self,run_id, x,y, color = 'blue'):
		p, = self.ax.plot(x,y, color=color)
		self.datasets.append( [p])
		self.dataset_ids.append(run_id)
		
	def step(self,run_id, x,y, color = 'blue'):
		p, = self.ax.step(x,y,where='post', color=color)
		self.datasets.append( [p])
		self.dataset_ids.append(run_id)	
	
	def show(self):
		self.dataset_labels = map(lambda i: 'run %i'%i, self.dataset_ids)

		plt.legend(map(operator.itemgetter(0), self.datasets), self.dataset_labels)

		plt.subplots_adjust(left=0.2)
		rax = plt.axes([0.05, 0.4, 0.1, 0.15])
		
		check = CheckButtons(rax, self.dataset_labels, [True]*len(self.dataset_ids))
		
		def func(label):
			index = self.dataset_labels.index(label)
			map( lambda p: p.set_visible(not p.get_visible()), self.datasets[index])
			plt.draw()
		
		check.on_clicked(func)
		plt.show()





class SMAC_analyzer(object):
   
	# collects smac specific data that goes into the scenario file
	def __init__(self, obj):
		
		if isinstance(obj,remote_smac.remote_smac):
			scenario_fn = os.path.join(obj.working_directory, 'scenario.dat')
		scenario_fn = str(obj)
		
		if isinstance(obj, six.string_types):
			scenario_fn=obj
		
		
		
		# parse scenario file for important information
		with open(scenario_fn) as fh:
			for line in fh.readlines():
				strlist = line.split()
				
				if strlist[0] == 'output-dir':
					self.output_dir = strlist[1]
				
				if strlist[0] == 'validation':
					self.validation = bool(strlist[1])
		
		# construct the folder name that contains all the run files
		self.scenario_dir = os.path.join(self.output_dir,reduce(str, scenario_fn.split('/')[-1].split('.')[:-1]))
		
		
		# find all the runs:
		run_files =  glob.glob(self.scenario_dir+'/live-rundata-*.json*')
		

		self.data_all_runs = []
		
		for f in run_files:
			
			with open(f,'r') as fh:
				data = [e for e in json_parse(fh)]
			
			def reduce_data( data):
				return {\
						'function value'     : data['r-quality'],
						'parameter settings' : data['r-rc']['rc-pc']['pc-settings'],
						'duration'           : data['r-wallclock-time']
						}
			
			run_id = int(re.match('.+live-rundata-(\d+)\.json$', f).group(1))
			run_data = [run_id] + map(reduce_data, data[1:])
			
			self.data_all_runs.append(run_data)

		self.cm = pltcm.rainbow(np.linspace(0,1,len(self.data_all_runs)))


	def get_item_all_runs(self, func = lambda d: d['function value']):
		return (map(lambda run: map(func, run[1:]), self.data_all_runs))
	
	def get_item_single_run(self, run_id, func = lambda d: d['function value']):
		return map(func,self.data_all_runs[run_id][1:])
	
	def plot_run_performance(self, runs = None):	

		plot = interactive_plot()
		
		for i in range(len(self.data_all_runs)):
			y = self.get_item_single_run(i)
			x = range(len(y))
			plot.scatter(self.data_all_runs[i][0], x,y, self.get_item_single_run(i, func = lambda d: '\n'.join(['%s=%s'%(k,v) for (k,v) in d['parameter settings'].items() ]) ), color = self.cm[i])
		
		plot.add_datacursor()
		plot.show()

			
	def plot_run_incumbent(self, runs = None):	
		plot = interactive_plot()
		
		for i in range(len(self.data_all_runs)):
			y = np.minimum.accumulate(self.get_item_single_run(i))
			#x = 
			_ , indices = np.unique(y, return_index = True)
			print(indices)
			
			indices = np.append(indices[::-1], len(y)-1)
			print(indices)
			x = np.arange(len(y))[indices]
			y = y[indices]
			
			print(x,y)
			print('='*40)
			plot.step(self.data_all_runs[i][0], x, y, color = self.cm[i])
		
		plot.add_datacursor(formatter = 'iteration {x:.0f}: {y}'.format)
		plot.show()
		
		
	def basic_analysis (self):
		
		fig, ax = plt.subplots()
		
		ax.set_title('function value vs. number of iterations')
		ax.set_xlabel('iteration')
		ax.set_ylabel('function value')
		
		for i in range(len(self.trajectory)):
			color='red' if i == self.incumbent_index else 'blue'
			ax.scatter( i, self.trajectory[i][0], color=color, label = '\n'.join(['%s = %s' % (k,v) for (k, v) in self.trajectory[i][2].items()]))

		datacursor(
			bbox=dict(alpha=1),
			formatter = 'iteration {x:.0f}: {y}\n{label}'.format,
			hover=False,
			display='multiple',
			draggable=True,
			horizontalalignment='center',
			hide_button = 3)
		
		
		fig, ax = plt.subplots()
		incumbents = np.minimum.accumulate(map(itemgetter(0), self.trajectory))
		ax.step(range(len(incumbents)), incumbents)
		
		
		plt.show()



if __name__ == "__main__":
	analyzer = SMAC_analyzer('/home/sfalkner/bitbucket/pysmac2/spysmac_on_minisat/scenario.dat')

