import boto3
import json
import os
from modules import user
from modules import errors
from urllib.parse import unquote

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

        elif http_method == "GET" and resource_path.endswith("profile"):

            authenticating_user = user.User(event['cognitoPoolClaims']['sub'])
            
            user_details = dict()

            subscription_data = authenticating_user.get_foundations_subscription()

            if subscription_data:

                for key in list(subscription_data["personalDetails"]):

                    user_details[key] = subscription_data["personalDetails"][key]["field"]["value"]

                user_details["foundationsID"] = subscription_data["foundationsId"]

            else:
        
                try:
                    user_details["foundationsID"] = authenticating_user.get_did()
                except errors.DIDNotFound:
                    user_details["foundationsID"] = None

            
            user_details["lastName"] = authenticating_user.last_name
            user_details["emailAddress"] = authenticating_user.email_address

            if not user_details.get("firstName"):
                user_details["firstName"] = authenticating_user.first_name
            if not user_details.get("lastName"):
                user_details["lastName"] = authenticating_user.last_name
            if not user_details.get("emailAddress"):
                user_details["emailAddress"] = authenticating_user.email_address


            status_code = 200
            return_body = user_details

        elif http_method == "GET" and resource_path.endswith("history"):

            authenticating_user = user.User(event['cognitoPoolClaims']['sub'])

            document_versions = authenticating_user.get_uploaded_document_versions()

            projects = authenticating_user.get_projects()

            signed_documents = authenticating_user.get_signed_documents()

            status_code = 200
            return_body = dict(
                documentVersions=document_versions,
                projects=projects,
                signedDocuments=signed_documents
            )

            print(return_body)

    # catch any application errors
    except errors.ApplicationError as error:
        return {
            'statusCode': 400,
            "Error": error.get_error_dict()
        }
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
                #"sub": "b966f0b7-4310-4608-b08d-418210e7ff20"
                "sub": "ca543d7c-7970-48ce-b100-9cf3f7c62aef"
            }
        },
        "get-profile": {
            "requestPath": "/user/profile",
            "method": "GET", 
            "cognitoPoolClaims": {
                #"sub": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa"
                #"sub": "778bd486-4684-482b-9565-1c2a51367b8c"
                "sub": "b966f0b7-4310-4608-b08d-418210e7ff20"
            }
        },
        "get-history": {
            "requestPath": "/user/get-history",
            "method": "GET", 
            "cognitoPoolClaims": {
                #"sub": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa"
                #"sub": "778bd486-4684-482b-9565-1c2a51367b8c"
                "sub": "ab0ae262-eedf-41c0-ac6e-e5109217b6c1"
            }
        }

    }



    print(lambda_handler(event["get-history"], {}))

        
