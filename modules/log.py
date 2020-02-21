import json
import logging
import os
import sys


logger = logging.getLogger()
# fh = logging.FileHandler('testlog.log')
# fh.setLevel(logging.DEBUG)
# logger.addHandler(fh)



def function_name():
    return sys._getframe(2).f_code.co_name

def module_name():

    try:
        module_path = sys._getframe(2).f_code.co_filename
        module_name = module_path.split('/')[-1].split('.py')[0]
    except:
        module_name = None

    return module_name

def filter_types(dict_in, types=[str, int, dict, list, bool, set]):

    filtered_variables = {}

    for name, value in dict_in.items():
        if type(dict_in[name]) in types:
            filtered_variables[name] = value

    return filtered_variables

# def get_local_variables():


def function_start_output():
    return 'Calling {}.{}'.format(module_name(), function_name())

def function_end_output(unfiltered_variables):
    return 'Variables at end of function {}.{}: {}'.format(module_name(),
                                                           function_name(),
                                                           filter_types(unfiltered_variables))


def set_logging_level(level='ERROR'):
    """
    Currently sets logging level to the level given. 
    Or to WARNING if no level is given.
    
    In future, this could log according to a level set at:

    User level (DID or Cognito Username), Function level, Stage level or Application level
    Whichever is highest.
    """
    
    # Is log level set in the environment?
    env_log_level = os.environ.get('PRIND_LOG_LEVEL', 'CRITICAL')

    # Was log level specified in teh 
    if level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        raise ValueError('Invalid log level given')

    resulting_level = min(eval('logging.{}'.format(l)) for l in [env_log_level, 
                                                                 level])

    logger.setLevel(resulting_level)

    logger.info('logging level set to {}'.format(logger.getEffectiveLevel()))



