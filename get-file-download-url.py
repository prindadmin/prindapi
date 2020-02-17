'''
This module uses the Session Token Service (STS) to create tokens for uploading
files to the S3 buckets for 1 hour
'''
import boto3
import json
import os

from modules import page
from modules import errors
from modules import document


def lambda_handler(event, context):

    #jwt_token = event['headers']['Authorization']
    try:
        cognito_username = event['cognitoPoolClaims']['sub']
        s3_bucket_arn = os.environ['S3_BUCKET_ARN']
        s3_bucket_name = os.environ.get("S3_BUCKET_NAME", "prind-portal-user-files-dev")

        print(cognito_username)

        # #Connect to the STS system
        s3_client = boto3.client('s3')

        project_id = event['path']['project_id']
        page_name = event['path']['page']
        field_index = event['path']['field_index']
        version = event['path']['version']

        this_page = page.Page(page_name, project_id)

        field = this_page.get_field(field_index)

        field_type = field['type']
        print('field type', field_type)
        
        if field_type != 'file':
            raise errors.InvalidFieldType('The field given is not a document field')

        try:
            document_did = field['fieldDetails']['documentDid']
        except KeyError:
            raise Exception('file field does not contain a document_did')

        print(document_did)

        this_document = document.Document(document_did)

        s3_version = this_document.get_version(version)['s3VersionId']

        print(s3_version)

        if not this_page.user_has_permission(cognito_username):
            raise errors.InsufficientPermission('User does not have permission to this project')

        # Create the policy to allow users to add files to their s3 bucket

        object_name = f"{project_id}/{page_name}/{field_index}"

        print('object_name', object_name)

        response = s3_client.generate_presigned_url('get_object',
                                                        Params={'Bucket': s3_bucket_name,
                                                                'Key': object_name,
                                                                'VersionId':s3_version},
                                                        ExpiresIn=3600)

        url = response

    except:
        raise

    return {
        "statusCode": 200,
        "body": {
            "url": url
        }
    }
     
if __name__ == '__main__':

    event = {
        "path": {
            "project_id": "ProjectNumberFour",
            "page": "inception",
            "field_index": 1,
            "version": 1
        },
        "cognitoPoolClaims": {
            "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
    }
    }

    print(lambda_handler(event, {}))
        

