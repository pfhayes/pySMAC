def read_scenario_file(fn):
    scenario_dict = {}
    with open(fn, 'r') as fh:
        for line in fh.readlines():
            if "=" in line:
                tmp = line.split("=")
                tmp = [' '.join(s.split()) for s in tmp]
            else:
                tmp = line.split()
            scenario_dict[tmp[0]] = " ".join(tmp[1:])
    return(scenario_dict)