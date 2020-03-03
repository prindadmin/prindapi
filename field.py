import boto3
import json
import os
import hashlib
import requests

from modules import errors
from modules import page
from modules import auth
from modules import document
from modules import field as field

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from urllib.parse import unquote
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

s3 = boto3.client('s3')

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

        project_id = unquote(event['path']['project_id'])
        page_name = unquote(event['path']['page'])
        field_index = int(event['path']['field_index'])

        field_data = event['body']['fieldDetails']
        title = event['body'].get('title')
        description = event['body'].get('description') 
        editable = event['body'].get('editable')

        this_field = field.Field(field_index=field_index, page_name=page_name, project_id=project_id)
        this_field_value = this_field.get() 

        field_type = this_field_value["type"]

        print(this_field_value)

        if field_type == "file":

            authenticating_username = event['cognitoPoolClaims']['sub']

            s3_bucket_name = os.environ.get("S3_BUCKET_NAME", "prind-portal-user-files-dev")
            s3_bucket_arn = os.environ.get("S3_BUCKET_ARN", "arn:aws:s3:::prind-portal-user-files-dev")
            api_id = os.environ["FOUNDATIONS_API_ID"]
            sp_did = os.environ["SP_DID"]
            api_stage = os.environ["FOUNDATIONS_API_STAGE"]

            s3_key = f"{project_id}/{page_name}/{field_index}"

            print(s3_key)

            foundations_jwt = auth.get_foundations_jwt(sp_did)

            document_tags = field_data.get('tags', [])
            filename = field_data['filename']

            try:
                this_document = document.Document(
                    project_id=project_id,
                    page=page_name,
                    field_index=field_index
                )
            except errors.DocumentNotFound:
                document_did = None
                action = "create"
            else:
                document_did = this_document.document_did
                action = "update"

            logger.info(f"document_did {document_did}")
            logger.info(f"action is: {action}")

            try:
                response = s3.get_object(Bucket=s3_bucket_name, Key=s3_key)
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    logger.error(f"The s3 key {s3_key} was not found")
                    raise errors.FileNotFound(f"The s3 key {s3_key} was not found")
                else:
                    logger.error(f"error {e.response['Error']['Code']} in call to s3.get_object()")
                    raise

            uploaded_file = response['Body']
            s3_version_id = response['VersionId']

            print("s3_version_id is:", s3_version_id)

            file_bytes = uploaded_file.read()    
            file_hash = hashlib.sha256(file_bytes).hexdigest();

            document_name = f"{project_id}/{page_name}/{field_index}"

            datetime_suffix = datetime.utcnow().isoformat()

            if action == "create":

                document_did = document.create(
                    project_id=project_id,
                    page=page_name,
                    field_index=field_index,
                    file_hash=file_hash, 
                    uploading_username=authenticating_username, 
                    s3_version_id=s3_version_id, 
                    s3_bucket_name=s3_bucket_name, 
                    s3_key=s3_key, 
                    filename=filename, 
                    document_name=document_name,
                    document_tags=document_tags
                )

           
            elif action == "update":

                this_document = document.Document(
                    project_id=project_id, 
                    page=page_name, 
                    field_index=field_index
                )

                this_document.update(
                    file_hash, 
                    authenticating_username, 
                    s3_version_id, 
                    filename
                )

            
        else: # this is not a file field
            
            this_page = page.Page(page=page_name, project_id=project_id)

            this_page.write_field(
                field_index=field_index, 
                field_data=field_data, 
                title=title, 
                description=description, 
                field_type=field_type, 
                editable=editable
            )

    # catch any application errors
    except errors.ApplicationError as error:
        raise
        # return {
        #     'statusCode': 400,
        #     "Error": error.get_error_dict()
        # }
    # catch unhandled exceptions
    # except Exception as e:
        
    #     # logger.error(log.logging.exception("message"))

    #     return {
    #         'statusCode': 500,
    #         'Error': errors.UnhandledException(context.log_group_name, context.log_stream_name, context.aws_request_id).get_error_dict()
    #     }

    
    return {
        "statusCode": 200,
        "body": "completed"
    }


if __name__ == '__main__':

    event = {
        "dropdown": {
            "cognitoPoolClaims": {
                "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
            },
            "path": {
                "project_id": "ProjectNumberFour",
                "page": "feasibility",
                "field_index": 2
            },
            "body": {
                "fieldDetails": {
                  "dropdownValue": "No",
                  "textboxValue": ".",
                  "dropdownOptions": [
                    {
                      "id": "1",
                      "name": "Yes"
                    },
                    {
                      "id": "2",
                      "name": "No"
                    }
                  ],
                  "optionOpensTextBox": "Yes"
                },
                "title": "This is a test drop-down box", 
                "description": "This is a test field",
                "type": "dropdown",
                "editable": True
            }
        },
        "file": {
            "cognitoPoolClaims": {
                "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
            },
            "path": {
                "project_id": "ProjectNumberSix",
                "page": "inception",
                "field_index": 1
            },
            "body": {
                "fieldDetails": {
                    "filename": "test.pdf",
                    "tags": []
                },
            }
        }
    }

    print(lambda_handler(event["file"], {}))