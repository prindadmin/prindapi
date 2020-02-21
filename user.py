import boto3
import json
import os
from modules import user
from modules import errors
from urllib.parse import unquote

def lambda_handler(event, context):

    try:
        
        resource_path = event['requestPath']
        http_method = event['method']

        print(event)

        # get project invitatons
        if http_method == "GET" and resource_path.endswith("get-project-invitations"):
            
            authorizing_username = event['cognitoPoolClaims']['sub']

            this_user = user.User(authorizing_username)

            invitations = this_user.get_project_invitations()

            status_code = 200
            return_body = invitations

        elif http_method == "GET" and resource_path.endswith("get-accessible-projects"):

            #jwt_token = event['headers']['Authorization']
            cognito_username = event['cognitoPoolClaims']['sub']

            this_user = user.User(cognito_username)

            projects = this_user.get_projects()
                 
            status_code = 200
            return_body = projects

        elif http_method == "GET" and resource_path.endswith("get-signature-requests"):

            authenticating_user = user.User(event['cognitoPoolClaims']['sub'])
            
            signing_requests = authenticating_user.get_signature_requests()

            status_code = 200
            return_body = signing_requests

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
        "statusCode": status_code,
        "body": return_body
    }

if __name__ == '__main__':

    event = {
        "get-project-invitations": {
            "requestPath": "/user/get-project-invitations",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub": "f9c255cb-a42b-4359-a8bd-2ebec5dfa2fa"
            }
        },
        "get-accessible-projects": {
            "requestPath": "/user/get-accessible-projects",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
            }
        },
        "get-signature-requests": {
            "requestPath": "/user/get-signature-requests",
            "method": "GET", 
            "cognitoPoolClaims": {
                #"sub": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa"
                "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
            }
        }
    }



    print(lambda_handler(event["get-signature-requests"], {}))

        
