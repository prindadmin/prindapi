import boto3
import json
import os
from modules import project
from modules import errors
from modules import role
from modules import user
from modules import did
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

        authenticating_username = event['cognitoPoolClaims']['sub']

        if http_method == "GET" and 'accreditation' in resource_path:

            foundations_id = event['path']['project_id']
            this_project = project.Project(foundations_id)

            if not this_project.user_in_roles(authenticating_username, ["*"]):
                raise errors.InsufficientPermission("You do not have permission to this project")

            subject_did_obj = did.Did(unquote(event['path']['foundations_id']))
            subject_username = subject_did_obj.get_cognito_username()

            if not this_project.user_in_roles(subject_username, ["*"]):
                raise errors.InsufficientPermission(f"{foundations_id} is not part of this project")

            subject_user_obj = user.User(subject_username)

            if subject_user_obj.first_name == 'Ben' and subject_user_obj.last_name == 'Jeater':

                return_body = [
                    {
                        "accreditationName": "Construction Basics 1",
                        "issuedDate": 1605213908,
                        "issuer": "Acme Inc",
                        "entryHash": "ee7514c2fe963160255645932f9f72416814b92a045b8dbba4ef6fb40b0c97d8"
                    }
                ]
            else:
                return_body = []

            status_code = 200

        else:
            return_body = "invalid path"
            status_code = 400


    # catch any application errors
    except errors.ApplicationError as error:
        return {
            'statusCode': 400,
            "Error": error.get_error_dict()
        }
    # catch unhandled exceptions
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
        "get-accreditations": {
            "requestPath": "/project/TestProject2020-02-27/accreditation/did:fnds:12345678",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub": "6a628546-9b4e-4c43-96a4-4e30c3c37511"
            },
            "path": {
                "project_id": "NewDayNewProject2020-03-05"
            }
        }
    }

    print(lambda_handler(event["get-accreditations"], {}))

    
