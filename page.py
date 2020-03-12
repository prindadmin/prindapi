import boto3
import json
import os

from modules import errors
from modules import page
from modules import project

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from urllib.parse import unquote

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

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

        project_id = unquote(event['path']['project_id'])
        page_name = unquote(event['path']['page'])
        authenticating_username = event['cognitoPoolClaims']['sub']
        this_project = project.Project(project_id)

        if http_method == "GET":

            if not this_project.user_in_roles(authenticating_username, ["*"]):
                raise errors.InsufficientPermission("You do not have permission to load a page from this project")

            try:
                this_page = page.Page(page=page_name, project_id=project_id)
                page_fields = this_page.get_resultant_fields()
            except errors.PageNotFound:
                page_fields = []

            return_body = page_fields
            status_code = 200  

        elif http_method == "POST" and resource_path.endswith("create-field"):

            if not this_project.user_in_roles(authenticating_username, ["*"]):
                raise errors.InsufficientPermission("You do not have permission to load a page from this project")

            this_page = page.Page(page=page_name, project_id=project_id)
            highest_field_index = this_page.get_highest_field_index()
            new_field_index = highest_field_index + 1

            field_data = event['body'].get('fieldDetails')
            title = event['body'].get('title')
            description = event['body'].get('description') 
            editable = event['body'].get('editable')

            try:
                field_type = event['body']['type']
            except KeyError:
                raise errors.MissingRequiredFields("type needs to be specified for a custom field")

            if not field_data: field_data = {}
            if not description: description = "."
            if not editable: editable = True
            if not title: title = "New Custom Field"
            
            this_page.write_field(
                field_index=new_field_index, 
                field_data=field_data, 
                title=title, 
                description=description, 
                field_type=field_type, 
                editable=editable
            )

            return_body = "completed"
            status_code = 201
  

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
        "get-page": {
            "requestPath": "/project/NewDayNewProject2020-03-05/inception",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub": "ab0ae262-eedf-41c0-ac6e-e5109217b6c1"
            },
            "path": {
                "project_id": "NewDayNewProject2020-03-05",
                "page": "inception"
            }
        },
        "create-field": {
            "requestPath": "/project/NewDayNewProject2020-03-05/inception/create-field",
            "method": "POST", 
            "cognitoPoolClaims": {
                "sub": "ab0ae262-eedf-41c0-ac6e-e5109217b6c1"
            },
            "path": {
                "project_id": "NewDayNewProject2020-03-05",
                "page": "inception"
            },
            "body": {
                "title": "Will any parts of the building / site be occupied during the works?",
                "description": "This is asked to ensure that any plans will take into account any members of the public who might be moving around the building / site.",
                "type": "file",
                "editable": True,
                "fieldDetails": {
                }
            }
        }
    }

    print(lambda_handler(event["get-page"], {}))