import re

def read_pcs(filename):
    ''' Function to read a SMAC pcs file (format according to version 2.08).
    
    :param filename: name of the pcs file to be read
    :type filename: str
    :returns: tuple -- (parameters as a dict, conditionals as a list, forbiddens as a list)
    '''
    
    num_regex = "[+\-]?(?:0|[1-9]\d*)(?:\.\d*)?(?:[eE][+\-]?\d+)?"
    FLOAT_REGEX = re.compile("^[ ]*(?P<name>[^ ]+)[ ]*\[(?P<range_start>%s)[ ]*,[ ]*(?P<range_end>%s)\][ ]*\[(?P<default>[^#]*)\](?P<misc>.*)$" %(num_regex,num_regex))
    CAT_REGEX = re.compile("^[ ]*(?P<name>[^ ]+)[ ]*{(?P<values>.+)}[ ]*\[(?P<default>[^#]*)\](?P<misc>.*)$")
    COND_REGEX = re.compile("^[ ]*(?P<cond>[^ ]+)[ ]*\|[ ]*(?P<head>[^ ]+)[ ]*in[ ]*{(?P<values>.+)}(?P<misc>.*)$")
    FORBIDDEN_REGEX = re.compile("^[ ]*{(?P<values>.+)}(?P<misc>.*)$")
        
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
                values = set([x.strip(" ") for x in cat_match.group("values").split(",")])
                default = cat_match.group("default")
                
                #logging.debug("CATEGORIAL: %s %s {%s} (%s)" %(name, default, ",".join(map(str, values)), type_))
                param_dict[name] = (values, default) 
                
            float_match = FLOAT_REGEX.match(line)
            if float_match:
                name = float_match.group("name")
                values = [float(float_match.group("range_start")), float(float_match.group("range_end"))]
                default = float(float_match.group("default"))
                
                #logging.debug("PARAMETER: %s %f [%s] (%s)" %(name, default, ",".join(map(str, values)), type_))
                param_dict[name] = (values, default)
                if "i" in float_match.group("misc"):
                    param_dict[name] += ('int',)
                if "l" in float_match.group("misc"):
                    param_dict[name] += ('log',)
                
            cond_match = COND_REGEX.match(line)
            if cond_match:
                #logging.debug("CONDITIONAL: %s | %s in {%s}" %(cond, head, ",".join(values)))
                conditions.append(line)
                
            forbidden_match = FORBIDDEN_REGEX.match(line)
            if forbidden_match:
                #logging.debug("FORBIDDEN: {%s}" %(values))
                forbiddens.append(line)
            
    return param_dict, conditions, forbiddens


def read_scenario_file(fn):
    """ Small helper function to read a SMAC scenario file.
    
    :returns : dict -- (key, value) pairs are (variable name, variable value)
    """
    scenario_dict = {}
    with open(fn, 'r') as fh:
        for line in fh.readlines():
            #remove comments
            if line.find("#") > -1:
                line = line[:line.find("#")]
            
            # skip empty lines
            if line  == "":
                continue
            if "=" in line:
                tmp = line.split("=")
                tmp = [' '.join(s.split()) for s in tmp]
            else:
                tmp = line.split()
            scenario_dict[tmp[0]] = " ".join(tmp[1:])
    return(scenario_dict)
