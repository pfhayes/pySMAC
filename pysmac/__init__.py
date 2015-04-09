from .optimizer import *
from .analyzer import *



# check for an appropriate JAVA version for SMAC

def check_java_version():
    import re
    from subprocess import STDOUT, check_output
    out = check_output(["java", "-version"], stderr=STDOUT).strip().split(b"\n")
    print(out)
    if len(out) < 1:
        print("Failed checking Java version. Make sure Java version 7 or greater is installed.")
        return False
    m = re.match(b'java version "\d+.(\d+)..*', out[0])
    if m is None or len(m.groups()) < 1:
        print ("Failed checking Java version. Make sure Java version 7 or greater is installed.")
        return False
    java_version = int(m.group(1))
    if java_version < 7:
        error_msg = "Found Java version %d, but Java version 7 or greater is required." % java_version
 
        raise RuntimeError(error_msg)

check_java_version()