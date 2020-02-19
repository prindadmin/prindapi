import boto3
import json
import os
from modules import user
from modules import errors
from urllib.parse import unquote

def lambda_handler(event, context):

    try:

        authorizing_username = event['cognitoPoolClaims']['sub']

        this_user = user.User(authorizing_username)

        invitations = this_user.get_project_invitations()

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
        "statusCode": 200,
        "body": invitations
    }

if __name__ == '__main__':

    event = {
        "cognitoPoolClaims": {
            "sub": "f9c255cb-a42b-4359-a8bd-2ebec5dfa2fa"
        }
    }

    print(lambda_handler(event, {}))

        
