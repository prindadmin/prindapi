import boto3
import json
import os
import hashlib
import requests

from modules import errors
from modules import auth
from modules import document
from modules import page

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

s3 = boto3.resource('s3')

def lambda_handler(event, context):

    try:
 
        cognito_username = event['cognitoPoolClaims']['sub']

        s3_bucket_name = os.environ.get("S3_BUCKET_NAME", "prind-portal-user-files-dev")
        s3_bucket_arn = os.environ.get("S3_BUCKET_ARN", "arn:aws:s3:::prind-portal-user-files-dev")
        api_id = os.environ["FOUNDATIONS_API_ID"]
        sp_did = os.environ["SP_DID"]
        api_stage = os.environ["FOUNDATIONS_API_STAGE"]
        
        project_id = event['body'].get('projectId')
        page_name = event['body'].get('page')
        field_index = event['body'].get('fieldIndex')
        title = event['body'].get('title')
        description = event['body'].get('description')

        document_did = event['path']['document_did']
        s3_version_id = event['body']['s3VersionId']

        foundations_jwt = auth.get_foundations_jwt(sp_did)
        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{document_did}/update"

        document_version = document.Document(document_did)

        object_version = s3.ObjectVersion(
            s3_bucket_name, 
            document_version.s3_key, 
            s3_version_id
        )    
        
        response = object_version.get()

        uploaded_file = response['Body']
     
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
                "s3VersionId": s3_version_id,
                "versionNumber": document_version_number,
                "uploadedBy": cognito_username
            }
        )

        table.put_item(
            Item={    
                "pk": f"document_v{document_version_number}_{document_did}",
                "sk": "documentVersion",
                "s3VersionId": s3_version_id,
                "versionNumber": document_version_number,
                "uploadedBy": cognito_username
            }
        )

        # update title and description if specified
        if page_name and field_index and project_id:
            this_page = page.Page(page_name, project_id)
            this_page.write_field(
                field_type="file",
                field_index=field_index,
                title=title,
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
        "body": "completed"
    }


if __name__ == '__main__':

    event = {
        "cognitoPoolClaims": {
            "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
        },
        "path": {
            "document_did": "did:fnds:c25eb417ffa90f8fedf29b385fc91f58831a470805f38474bd71f327b860f946"
        },
        "body": {
            "s3VersionId": "aACPyGfvlK5VOKq4fDKaw6kcmMAz3diX",
            "projectId": "ProjectNumberFour",
            "page": "inception",
            "fieldIndex": 1
        }
    }

    # "documentDid": "did:fnds:fb926075aec4f9108cf79689680dd085257daaf50d7eb635252c03fcf9666af6"
    #{'documentDid': 'did:fnds:245a22623f2f10cadf0d02c052f41ac44dfcfd6621f02f488b4a7b724154e1de'}
    lambda_handler(event, {})