import boto3
import json
import os
from modules import project
from modules import errors

def lambda_handler(event, context):

    try:

        body = event['body']

        authorizing_username = event['cognitoPoolClaims']['sub']

        project.create_project(
            project_name=body.get('name'),
            project_creator=authorizing_username,
            project_description=body.get('description'),
            site_address=body.get('siteAddress'),
            occupied_during_works=body.get('occupiedDuringWorks'),
            workplace_when_completed=body.get('workplaceWhenComplete') 
        )

    # catch any application errors
    except errors.ApplicationError as error:
        return {
            "statusCode": 400,
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
        "statusCode": 201,
        "body": "completed"
    }

        
