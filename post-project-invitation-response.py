import boto3
import json
import os
from modules import project
from modules import errors
from urllib.parse import unquote

def lambda_handler(event, context):

    try:

        this_project = project.Project(unquote(event['path']['project_id']))
        authorizing_username = event['cognitoPoolClaims']['sub']

        this_project.respond_to_invitation(
                username=authorizing_username,
                accepted=event['body']['accepted']
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
            "sub": "f9c255cb-a42b-4359-a8bd-2ebec5dfa2fa"
        },
        "body": {
            "accepted": True
        }
    }

    lambda_handler(event, {})

        
