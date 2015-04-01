#! /bin/python
import resource
import signal
import multiprocessing
import sys
import os

class abort_function (Exception): pass


# create the function the subprocess can execute
def subprocess_func(func, pipe, mem_in_mb, time_limit_in_s, num_procs = None, *args, **kwargs):

    logger = multiprocessing.get_logger()

    os.setpgrp()

    # simple signal handler to close the pipe if a signal is is caught
    def handler(signum, frame):
        logger.debug("received signal number %i. Exiting uncracefully."%signum)
        raise abort_function
	

    # set the memory limit
    if mem_in_mb is not None:
        mem_in_b = mem_in_mb*1024*1024
        resource.setrlimit(resource.RLIMIT_AS, (mem_in_b, mem_in_b))

    # for now: don't allow the function to spawn subprocesses itself.
    #resource.setrlimit(resource.RLIMIT_NPROC, (1, 1))
    # Turns out, this is quite restrictive, so we don't use this option by default
    if num_procs is not None:
        resource.setrlimit(resource.RLIMIT_NPROC, (num_procs, num_procs))


    # schedule an alarm in specified number of seconds
    if time_limit_in_s is not None:
        signal.alarm(time_limit_in_s)

        # one could also limit the actual CPU time, but that does not help if the process hangs, e.g., in a dead-lock
        #resource.setrlimit(resource.RLIMIT_CPU, (time_limit_in_s,time_limit_in_s))

    signal.signal( signal.SIGALRM, handler)
    signal.signal( signal.SIGTERM, handler)

    return_value=None;

    # the actual function call
    try:
        logger.warning('call to your function')
        return_value = func(*args, **kwargs)
        logger.warning('function returned %s'%str(return_value))

    except MemoryError:
        logger.warning("Function call with the arguments %s, %s has exceeded the memory limit!"%(args,kwargs))

    except OSError as e:
        if (e.errno == 11):
            logger.waring("Your function tries to spanwn too many subprocesses/threads.")
        else:
            logger.warning('Something fishy going on here!')
            raise;

    except abort_function:
        logger.warning('Your function call was aborted. It probably took too long.')

    except:
        logger.warning('The call to your function did not return properly!\n%s\n%s', args, kwargs)
        raise;

    finally:
        pipe.send(return_value)
        pipe.close()

def enforce_limits (mem_in_mb=None, time_in_s=None, grace_period_in_s = 1):
    logger = multiprocessing.get_logger()
    
    if mem_in_mb is not None:
        logger.debug("restricting your function to %i mb memory."%(mem_in_mb))
    if time_in_s is not None:
        logger.debug("restricting your function to %i seconds runtime."%(time_in_s))


	
    def actual_decorator(func):

        def wrapped_function(*args, **kwargs):

            # create a pipe to retrieve the return value
            parent_conn, child_conn = multiprocessing.Pipe()

            # create and start the process
            subproc = multiprocessing.Process(target=subprocess_func, name="Call to your function", args = (func, child_conn,mem_in_mb, time_in_s) + args ,kwargs = kwargs)
            logger.debug("Your function is called now.")
            subproc.start()
            
            if time_in_s is not None:
                # politely wait for it to finish
                subproc.join(time_in_s + grace_period_in_s)

                # if it is still alive, send sigterm
                if subproc.is_alive():
                    logger.warning("Your function took to long, killing it now.")
                    #subproc.terminate()
                    
                    os.killpg(os.getpgid(subproc.pid),15)
                    subproc.join()
                    return(None)
            else:
                subproc.join()
            logger.debug("Your function has returned now with exit code %i."%subproc.exitcode)

			# if something went wrong, 
            if subproc.exitcode != 0:
                return(None)

            # return the function value from the pipe
            return (parent_conn.recv());

        return wrapped_function

    return actual_decorator

