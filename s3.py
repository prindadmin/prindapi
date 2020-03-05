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
from modules import project
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
        logger.info(f"event is {event}")

        if http_method == "GET" and resource_path.endswith("get-sts"):

            project_id = event['path']['project_id']
            this_project=project.Project(project_id)
            
            if not this_project.user_in_roles(authenticating_username, ["*"]):
                raise errors.InsufficientPermission("You do not have permission to upload files on this project")

            s3_bucket_arn = os.environ['S3_BUCKET_ARN']

            # #Connect to the STS system
            client = boto3.client('sts')
            page_name = event['path']['page']
            this_page = page.Page(page_name, project_id)

            #Create the policy to allow users to add files to their s3 bucket
            policy = json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid" : "VisualEditor0",
                        "Effect": "Allow",
                        "Action": [
                            "s3:PutObject",
                            "s3:GetObject"
                        ],
                        "Resource": [f"{s3_bucket_arn}/{this_page.project_id}/{this_page.page_name}/*"]
                    }
                ]
            })

            logger.info(f"created policy is {policy}")
            
            #Get tokens for user to assume the role
            response = client.assume_role(
                RoleArn = "arn:aws:iam::434494845257:role/webClientRole",
                Policy = policy,
                RoleSessionName = "webClientRole",
                DurationSeconds = 3600
            )
                  
            return_dict = {
                "SessionToken" : response["Credentials"]["SessionToken"],
                "Expiration" : response["Credentials"]["Expiration"].timestamp(),
                "AccessKeyId" : response["Credentials"]["AccessKeyId"], 
                "SecretAccessKey" : response["Credentials"]["SecretAccessKey"]
            }

            status_code = 200
            return_body = return_dict

        elif http_method == "GET" and resource_path.endswith("get-file-url"):

            project_id = unquote(event['path']['project_id'])
            this_project = project.Project(project_id)

            if not this_project.user_in_roles(authenticating_username, ["*"]):
                raise errors.InsufficientPermission("You do not have permission to download files on this project")

            s3_bucket_arn = os.environ['S3_BUCKET_ARN']
            s3_bucket_name = os.environ.get("S3_BUCKET_NAME", "prind-portal-user-files-dev")
            page_name = unquote(event['path']['page'])
            field_index = event['path']['field_index']
            version = event['path']['version']

            # #Connect to the STS system
            s3_client = boto3.client('s3')

            this_document = document.Document(
                project_id=project_id, 
                page=page_name, 
                field_index=field_index
            )

            s3_version = this_document.get_version(version)['s3VersionId']

            logger.info(f"s3_version is : {s3_version}")

            # Create the policy to allow users to add files to their s3 bucket
            object_name = f"{project_id}/{page_name}/{field_index}"

            logger.info(f"object_name: {object_name}")

            response = s3_client.generate_presigned_url('get_object',
                                                            Params={'Bucket': s3_bucket_name,
                                                                    'Key': object_name,
                                                                    'VersionId':s3_version},
                                                            ExpiresIn=3600)

            url = response

            status_code = 200
            return_body = url

        elif http_method == "GET" and resource_path.endswith("/get-sts/profile-avatar"):
            
            # TODO: New bucket ARN required
            s3_user_profiles_bucket_arn = os.environ['S3_USER_PROFILES_BUCKET_ARN']

            # #Connect to the STS system
            client = boto3.client('sts')

            #Create the policy to allow users to add files to their s3 bucket
            policy = json.dumps({
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid" : "VisualEditor0",
                        "Effect": "Allow",
                        "Action": [
                            "s3:PutObject",
                            "s3:GetObject"
                        ],
                        "Resource": [f"{s3_user_profiles_bucket_arn}/profile-avatar/{authenticating_username}"]
                    }
                ]
            })

            logger.info(f"created policy is {policy}")
            
            #Get tokens for user to assume the role
            response = client.assume_role(
                RoleArn = "arn:aws:iam::434494845257:role/webClientRole",
                Policy = policy,
                RoleSessionName = "webClientRole",
                DurationSeconds = 3600
            )
                  
            return_dict = {
                "SessionToken" : response["Credentials"]["SessionToken"],
                "Expiration" : response["Credentials"]["Expiration"].timestamp(),
                "AccessKeyId" : response["Credentials"]["AccessKeyId"], 
                "SecretAccessKey" : response["Credentials"]["SecretAccessKey"]
            }

            status_code = 200
            return_body = return_dict
   
   # catch any application errors
    except errors.ApplicationError as error:
        return {
            'statusCode': 400,
            "Error": error.get_error_dict()
        }

    return {
        "statusCode": status_code,
        "body": return_body
    }


if __name__ == '__main__':

    event = {
        "get-sts": {
            "requestPath": "/project/ProjectNumberFour/page/feasibility/get-sts",
            "method": "GET", 
            "path": {
                "project_id": "ProjectNumberFour",
                "page": "feasibility",
            },
            "cognitoPoolClaims": {
                "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
            }
        },
        "get-file-url": {
            "requestPath": "/project/ProjectNumberFour/inception/1/1/get-file-url",
            "method": "GET", 
            "path": {
                "project_id": "BenTest12020-02-26",
                "page": "inception",
                "field_index": 1,
                "version": 2
            },
            "cognitoPoolClaims": {
                "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
            }
        },
        "get-sts-profile-avatar": {
            "requestPath": "/user/get-sts/profile-avatar",
            "method": "GET", 
            "path": {},
            "cognitoPoolClaims": {
                "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
            }
        }
    }

    print(lambda_handler(event["get-sts-profile-avatar"], {}))
        

