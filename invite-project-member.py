import boto3
import json
import os
from modules import project
from modules import errors
from urllib.parse import unquote

def lambda_handler(event, context):

    try:

        body = event['body']
        this_project = project.Project(unquote(event['path']['project_id']))
        authorizing_username = event['cognitoPoolClaims']['sub']

        this_project.invite_user(
            requesting_user_name=authorizing_username,
            user_to_add=event['body']['username'],
            role_id=event['body']['roleId']
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

if __name__ == '__main__':

    event = {
        "path": {
            "project_id": "ProjectNumberFour"
        },
        "cognitoPoolClaims": {
            "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
        },
        "body": {
            "username": "f9c255cb-a42b-4359-a8bd-2ebec5dfa2fa",
            "roleId": "projectConsultant"
        }
    }

    lambda_handler(event, {})

        
