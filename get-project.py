import boto3
import json
import os
from modules import project
from modules import errors


def lambda_handler(event, context):

    try:

        this_project = project.Project(event['path']['project_id'])

        return_dict = {
            "Id": this_project.project_id,
            "name": this_project.project_name,
            "description": this_project.project_description,
            "siteAddress": this_project.site_address,
            "occupiedDuringWorks": this_project.occupied_during_works,
            "workplaceWhenCompleted": this_project.workplace_when_completed
        }

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
        "body": return_dict
    }
        

        
