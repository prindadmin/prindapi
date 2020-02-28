import boto3
import json
import os
import hashlib
import requests

from modules import errors
from modules import page
from modules import auth

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
        field_type = event['body']['type']
        editable = event['body'].get('editable')

        this_page = page.Page(page=page_name, project_id=project_id)
        this_field = this_page.get_field(field_index)

        print(this_field)

        if this_field["type"] != event['body']['type']:

            raise errors.InvalidFieldType("The field type is incorrect for this field")

        # # is this a document create/update?
        if this_field["type"] == "file":

            cognito_username = event['cognitoPoolClaims']['sub']

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

            if this_field.get("fileDetails") == []:
                document_did = None
            else:
                existing_field_details = this_field.get("fieldDetails", {})
                document_did = existing_field_details.get("documentDid")
   
            print("document_did", document_did)

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

            action = "update" if document_did else "create"

            document_name = f"{project_id}/{page_name}/{field_index}"

            datetime_suffix = datetime.utcnow().isoformat()

            print("action is", action)

            if action == "create":

                api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document/create"

                params = {
                    "documentName": document_name,
                    "documentHash": file_hash,
                    "requesterReference": "File Uploader"
                }

                response = requests.post(
                    api_url,
                    data=params,
                    headers={'Authorization': foundations_jwt}
                )

                response_dict = json.loads(response.content.decode('utf-8'))

                if not response.status_code == 202:
                    
                    print("status code was", response.status_code)
                    print("response content was", response_dict)
                    
                    raise Exception('API call failed')
                
                print(response_dict)

                document_did = response_dict['body']['documentDid']

                table.put_item(
                    Item={    
                        "pk": f"document_{document_did}",
                        "sk": "document",
                        "data": document_name,
                        "s3BucketName": s3_bucket_name ,
                        "s3Key": s3_key
                    }
                )

                table.put_item(
                    Item={    
                        "pk": f"document_{document_did}",
                        "sk": "documentProject",
                        "data": project_id 
                    }
                )

                table.put_item(
                    Item={    
                        "pk": f"document_v0_{document_did}",
                        "sk": "documentVersion",
                        "data": f"uploader_{cognito_username}_{datetime_suffix}",
                        "s3VersionId": s3_version_id,
                        "versionNumber": 1,
                        "filename": filename
                    }
                )

                table.put_item(
                    Item={    
                        "pk": f"document_v1_{document_did}",
                        "sk": "documentVersion",
                        "data": f"uploader_{cognito_username}_{datetime_suffix}",
                        "s3VersionId": s3_version_id,
                        "versionNumber": 1,
                        "filename": filename
                    }
                )

                for tag in document_tags:
                    table.put_item(
                        Item={    
                            "pk": f"document_{document_did}",
                            "sk": f"documentTag_{tag}",
                            "data": document_did 
                        }
                    )

           
            elif action == "update":

                api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{document_did}/update"

                # document_version = document.Document(document_did)
                # s3_key = document_version.s3_key

                response = s3.get_object(Bucket=s3_bucket_name, Key=s3_key)
                uploaded_file = response['Body']
                s3_version_id = response['VersionId']

                print("s3_version_id is:", s3_version_id)
                
                file_bytes = uploaded_file.read()    
                file_hash = hashlib.sha256(file_bytes).hexdigest();

                print(file_hash)

                params = {
                    "documentHash": file_hash,
                    "requesterReference": "File Uploader"
                }

                print(params)

                response = requests.post(
                    api_url,
                    data=params,
                    headers={'Authorization': foundations_jwt}
                )


                response_dict = json.loads(response.content.decode('utf-8'))

                if not response.status_code == 202:
                    
                    print("status code was", response.status_code)
                    print("response content was", response_dict)
                    
                    raise Exception('API call failed')
                

                print(response_dict)

                document_version_number = response_dict['body']['documentVersionNumber']

                table.put_item(
                    Item={    
                        "pk": f"document_v0_{document_did}",
                        "sk": "documentVersion",
                        "data": f"uploader_{cognito_username}_{datetime_suffix}",
                        "s3VersionId": s3_version_id,
                        "versionNumber": document_version_number,
                        "filename": filename
                    }
                )

                table.put_item(
                    Item={    
                        "pk": f"document_v{document_version_number}_{document_did}",
                        "sk": "documentVersion",
                        "data": f"uploader_{cognito_username}_{datetime_suffix}",
                        "s3VersionId": s3_version_id,
                        "versionNumber": document_version_number,
                        "filename": filename
                    }
                )

            
            # finally write the document field
            this_page.write_document_field(
                field_index=field_index,
                document_did=document_did,
                description=description
            )

        else: # this is not a file field
            
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
                "type": "file",
                "editable": True
            }
        }
    }

    print(lambda_handler(event["file"], {}))