import boto3
import json
import os
from modules import project
from modules import errors

def lambda_handler(event, context):

    try:

        body = event['body']
        this_project = project.Project(event['path']['project_id'])
        authorizing_username = event['cognitoPoolClaims']['sub']

        this_project.add_user_role(
            requesting_user_name=authorizing_username,
            user_to_add=body['user'],
            role_id=body['roleId']
        )

    # catch any application errors
    except errors.ApplicationError as error:
        raise
    #     return {
    #         'statusCode': 400,
    #         "Error": error.get_error_dict()
    #     }
    # # catch unhandled exceptions
    # except Exception as e:
        
    #     # logger.error(log.logging.exception("message"))

    #     return {
    #         'statusCode': 500,
    #         'Error': errors.UnhandledException(context.log_group_name, context.log_stream_name, context.aws_request_id).get_error_dict()
    #     }

    
    return {
        "statusCode": 201,
        "body": "completed"
    }

        
