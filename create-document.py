import boto3
import json
import os
import hashlib
import requests

from modules import errors
from modules import auth
from modules import project

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

s3 = boto3.client('s3')

def lambda_handler(event, context):

    try:
       
        s3_bucket_name = os.environ.get("S3_BUCKET_NAME", "prind-portal-user-files-dev")
        s3_bucket_arn = os.environ.get("S3_BUCKET_ARN", "arn:aws:s3:::prind-portal-user-files-dev")
        api_id = os.environ["FOUNDATIONS_API_ID"]
        sp_did = os.environ["SP_DID"]
        api_stage = os.environ["FOUNDATIONS_API_STAGE"]

        foundations_jwt = auth.get_foundations_jwt(sp_did)
        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document/create"

        
        document_name = event['body']['title']
        document_tags = event['body']['tags']
        project_id = event['body']['projectId']
        s3_key = event['body']['s3Key']
        s3_version_id = event['body']['s3VersionId']
        filename = event['body']['filename']


        # validate project
        document_project = project.Project(project_id)

        print('s3_bucket_name',s3_bucket_name,'s3_bucket_arn',s3_bucket_arn)

        response = s3.get_object(Bucket=s3_bucket_name, Key=s3_key)
        uploaded_file = response['Body']
     
        file_bytes = uploaded_file.read()    
        file_hash = hashlib.sha256(file_bytes).hexdigest();

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
        
        print(response_dict)

        document_did = response_dict['body']['documentDid']

        
        table.put_item(
            Item={    
                "pk": f"document_{document_did}",
                "sk": "document",
                "data": document_name,
                "s3BucketName": s3_bucket_name ,
                "s3Key": s3_key,
                "filename": filename,
                "versionNumber": 1
            }
        )

        for tag in document_tags:
            table.put_item(
                Item={    
                    "pk": f"document_{document_did}",
                    "sk": f"document-tag_{tag}",
                    "data": document_did 
                }
            )

        table.put_item(
            Item={    
                "pk": f"document_{document_did}",
                "sk": "document-project",
                "data": project_id 
            }
        )

        table.put_item(
            Item={    
                "pk": f"document_v0_{document_did}",
                "sk": "document-version",
                "s3VersionId": s3_version_id,
                "versionNumber": 1
            }
        )

        table.put_item(
            Item={    
                "pk": f"document_v1_{document_did}",
                "sk": "document-version",
                "s3VersionId": s3_version_id,
                "versionNumber": 1
            }
        )

    # catch any application errors
    except:
        raise

    # except errors.ApplicationError as error:
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
        "body": "completed"
    }


if __name__ == '__main__':

    event = {
        "body": {
            "title": "Test Document",
            "tags": ["Test", "Document"],
            "projectId": "ProjectNumberFour",
            "s3BucketName": "prind-portal-user-files-dev",
            "s3Key": "test-document.txt",
            "s3VersionId": '9fb119dd751a6bcda45f1be11d4cb49bea57e7f1e3419bfbeb5485cbe01ad8c6',
            "filename": 'test-document.txt'
        }
    }

    lambda_handler(event, {})