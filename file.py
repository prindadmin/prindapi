import boto3
import json
import os
from urllib.parse import unquote

from modules import log
from modules.log import logger
from modules.auth import ProcoreAuth
from modules import errors
from modules.procore_project import Project

try:
    stage_log_level = os.environ["LOG_LEVEL"]
except (NameError, KeyError):
    stage_log_level = "CRITICAL"

print("stage_log_level:", stage_log_level)

# set the log level
log.set_logging_level(stage_log_level)


def lambda_handler(event, context):

    try:

        resource_path = event["requestPath"]
        http_method = event["method"]

        authenticating_username = event["cognitoPoolClaims"]["sub"]

        if http_method == "GET" and resource_path.startswith("/procorefiles"):
            """
            Handles the endpoints where folder_id is specified
            and folder_id is not specified
            """
            company_id = event['path']['company_id']
            project_id = event['path']['project_id']
            folder_id = event['path'].get('folder_id')

            print('folder_id in lambda is', folder_id)

            this_project = Project(company_id, project_id)
            return_body = this_project.get_procore_files(
                authenticating_username,
                folder_id=folder_id
            )

            status_code = 200

        else:
            print(http_method)
            print(resource_path)
            return_body = {"Error": "invalid path"}
            status_code = 400

    # catch any application errors
    except errors.ApplicationError as error:
        return {"statusCode": 400, "Error": error.get_error_dict()}
    # # catch unhandled exceptions
    # except Exception as e:

    #     # logger.error(log.logging.exception("message"))

    #     return {
    #         'statusCode': 500,
    #         'Error': errors.UnhandledException(context.log_group_name, context.log_stream_name, context.aws_request_id).get_error_dict()
    #     }

    return {"statusCode": status_code, "body": return_body}


if __name__ == "__main__":

    # event = {
    #     'authoriseprocore': {
    #         "requestPath": "/user/authoriseprocore",
    #         "method": "POST",
    #         "cognitoPoolClaims": {
    #             "sub": "ab0ae262-eedf-41c0-ac6e-e5109217b6c1"
    #         },
    #         "path": {
    #             "project_id": "NewDayNewProject2020-03-05",
    #             "page": "inception"
    #         },
    #         'body': {
    #             'code': 'asdgag',
    #             'requestURI': 'http://localhost:3000/procore-auth',
    #         }
    #     },
    #     'checkprocore': {

    #     }
    # }

    pass

    # print(lambda_handler(event, {}))