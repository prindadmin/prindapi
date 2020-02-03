import boto3
import json
import os
from modules import project
from modules import errors



def lambda_handler(event, context):

    try:

        projects = project.list_all_projects()

    # catch any application errors
    except errors.ApplicationError as error:
        return {
            'statusCode': 400,
            "Error": error.get_error_dict()
        }
    # catch unhandled exceptions
    except Exception as e:
        
        # logger.error(log.logging.exception("message"))

        return {
            'statusCode': 500,
            'Error': errors.UnhandledException(context.log_group_name, context.log_stream_name, context.aws_request_id).get_error_dict()
        }

    
    return {
        "statusCode": 200,
        "body": projects
    }
        

        
