import re

def read_pcs(filename):
	''' reads pcs file format of SMAC (format according to version 2.08);
		returns parameters as dict;	conditionals and forbiddens as lists '''
	
	
	FLOAT_REGEX = re.compile("^[ ]*(?P<name>[^ ]+)[ ]*\[(?P<range_start>[0-9]+(\.[0-9]+)?)[ ]*,[ ]*(?P<range_end>[0-9]+(\.[0-9]+)?)\][ ]*\[(?P<default>[^#]*)\](?P<misc>.*)$")
	CAT_REGEX = re.compile("^[ ]*(?P<name>[^ ]+)[ ]*{(?P<values>.+)}[ ]*\[(?P<default>[^#]*)\](?P<misc>.*)$")
	COND_REGEX = re.compile("^[ ]*(?P<cond>[^ ]+)[ ]*\|[ ]*(?P<head>[^ ]+)[ ]*in[ ]*{(?P<values>.+)}(?P<misc>.*)$")
	FORBIDDEN_REGEX = re.compile("^[ ]*{(?P<values>.+)}(?P<misc>.*)*$")
		
	param_dict = {} # name -> ([begin, end], default, flags)
	conditions = []
	forbiddens = []
		
	with open(filename) as fp:
		for line in fp:
			#remove line break and white spaces
			line = line.strip("\n").strip(" ")
			
			#remove comments
			if line.find("#") > -1:
				line = line[:line.find("#")] # remove comments
			
			# skip empty lines
			if line  == "":
				continue
			
			# categorial parameter
			cat_match = CAT_REGEX.match(line)
			if cat_match:
				name = cat_match.group("name")
				values = map(lambda x: x.strip(" "), cat_match.group("values").split(","))
				default = cat_match.group("default")
				
				#logging.debug("CATEGORIAL: %s %s {%s} (%s)" %(name, default, ",".join(map(str, values)), type_))
				#TODO: type of "values"???
				param_dict[name] = (values, default) 
				
			float_match = FLOAT_REGEX.match(line)
			if float_match:
				name = float_match.group("name")
				values = [float(float_match.group("range_start")), float(float_match.group("range_end"))]
				default = float(float_match.group("default"))
				
				#logging.debug("PARAMETER: %s %f [%s] (%s)" %(name, default, ",".join(map(str, values)), type_))
				#TODO: list instead of tuple???
				param_dict[name] = [values, default]					
				if "i" in float_match.group("misc"):
					param_dict[name].append("int")
				if "l" in float_match.group("misc"):
					param_dict[name].append("log")
				
			cond_match = COND_REGEX.match(line)
			if cond_match:
				#logging.debug("CONDITIONAL: %s | %s in {%s}" %(cond, head, ",".join(values)))
				conditions.append(line)
				
			forbidden_match = FORBIDDEN_REGEX.match(line)
			if forbidden_match:
				#logging.debug("FORBIDDEN: {%s}" %(values))
				forbiddens.append(line)
			
	return param_dict, conditions, forbiddens
