import boto3
import json
import os
from modules import role
from modules import errors

from modules import log
from modules.log import logger

try:
    stage_log_level = os.environ['PRIND_LOG_LEVEL']
except (NameError, KeyError):
    stage_log_level = 'CRITICAL'

print('stage_log_level:', stage_log_level)

# set the log level
log.set_logging_level(stage_log_level)

def lambda_handler(event, context):


    try:
        logger.info(f'roles lambda called with event {event}')

        roles = role.list_all_roles()
    
    except errors.ApplicationError as error:
        return {
            'statusCode': 400,
            "Error": error.get_error_dict()
        }

    return {
        "statusCode": 200,
        "body": roles
    }
        

        
