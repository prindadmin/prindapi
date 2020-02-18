import boto3
import json
import os
import hashlib
import requests

from modules import errors
from modules import auth
from modules import project
from modules import page

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

s3 = boto3.client('s3')

def lambda_handler(event, context):

    try:

        cognito_username = event['cognitoPoolClaims']['sub']
       
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
        filename = event['body']['filename']
        page_name = event['body'].get('page')
        field_index = event['body'].get('fieldIndex')
        #s3_version_id = event['body'].get(['s3VersionId'])
        description = event['body'].get('description')

        # validate project
        document_project = project.Project(project_id)

        print('s3_bucket_name',s3_bucket_name,'s3_bucket_arn',s3_bucket_arn)

        response = s3.get_object(Bucket=s3_bucket_name, Key=s3_key)
        uploaded_file = response['Body']
        s3_version_id = response['VersionId']

        print("s3_version_id is:", s3_version_id)

     
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
                "s3Key": s3_key,
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
                "s3VersionId": s3_version_id,
                "versionNumber": 1,
                "uploadedBy": cognito_username
            }
        )

        table.put_item(
            Item={    
                "pk": f"document_v1_{document_did}",
                "sk": "documentVersion",
                "s3VersionId": s3_version_id,
                "versionNumber": 1,
                "uploadedBy": cognito_username
            }
        )

        # update the file field on the page
        if page_name and field_index and project_id:
            this_page = page.Page(page_name, project_id)
            this_page.write_document_field(
                field_index=field_index,
                document_did=document_did,
                title=document_name,
                description=description
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
        "body": {
            "documentDid": document_did,
            "versionId": s3_version_id
        }
    }


if __name__ == '__main__':

    event = {
        "cognitoPoolClaims": {
            "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
        },
        "body": {
            "title": "Test Document 2",
            "tags": ["Test", "Document", "2"],
            "projectId": "ProjectNumberFour",
            "s3BucketName": "prind-portal-user-files-dev",
            "s3Key": "test-document2.txt",
            "s3VersionId": '.O.H36bCD30kYbcTPZAILIUpnPxN74Jp',
            "filename": 'test-document.txt2',
            "page": "inception",
            "fieldIndex": 1  
        }
    }

    lambda_handler(event, {})