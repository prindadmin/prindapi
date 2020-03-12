import boto3
import os
import time
import requests
import json

from modules import errors
from modules import document
from modules import user
from modules import auth

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

        this_user = user.User(event['cognitoPoolClaims']['sub'])

        api_id = os.environ["FOUNDATIONS_API_ID"]
        sp_did = os.environ["SP_DID"]
        api_stage = os.environ["FOUNDATIONS_API_STAGE"]

        foundations_jwt = auth.get_foundations_jwt(sp_did)

        project_id = event["path"]["project_id"]
        page = event["path"]["page"]
        field_index = event["path"]["field_index"]

        requester_reference = event["body"].get("requesterReference")
        accepted = event["body"].get("accepted", True)

        document_obj = document.Document(project_id, page, field_index)
        
        if accepted:

            logger.info("The signing request was accepted")
    
            document_version = 0 # latest

            api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{document_obj.document_did}/signing-request/{document_version}"

            logger.info(f"api_url is: {api_url}")

            params = {
                "signingDid": this_user.get_did(),
            }

            if requester_reference:
                params['requesterReference'] = requester_reference

            logger.info(f"params: {params}")

            response = requests.post(
                api_url,
                data=params,
                headers={'Authorization': foundations_jwt}
            )

            response_dict = json.loads(response.content.decode('utf-8'))

            if response_dict.get("statusCode") != 201:
                logger.error(f"error calling /sp/document-did/{document_obj.document_did}/signing-request/{document_version}: ")
                raise errors.FoundationsApiError(f"error calling /sp/document-did/{document_obj.document_did}/signing-request/{document_version}")
            else:
                logger.info(f"response from /sp/document-did/{document_obj.document_did}/signing-request/{document_version} is {response_dict}")
  
        signing_request_key = {    
            "pk": f"user_{this_user.username}",
            "sk": f"documentSignRequest_{project_id}/{page}/{field_index}",
        }

        print(signing_request_key)

        response = table.delete_item(
            Key=signing_request_key,
            ReturnValues="ALL_OLD"
        )

        print(response)

        try:
            old_item = response["Attributes"]
        except KeyError:
            #raise errors.SigningRequestNotFound(f"The signing request was not found")
            logger.warning("a signing request was not found")
        else:
            new_item = old_item.copy()

            new_item["sk"] = f"documentSignRequestResponse_{project_id}/{page}/{field_index}"
            new_item["respondedAt"] = str(int(time.time()))
            new_item["accepted"] = accepted

            table.put_item(
                Item=new_item
            )    

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
        "statusCode": 200,
        "body": "completed"
    }


if __name__ == '__main__':

    event = {
        "cognitoPoolClaims": {
            "sub": "ab0ae262-eedf-41c0-ac6e-e5109217b6c1"
            #"sub": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa"
        },
        "body": {
            "accepted": False
        },
        "path": {
            #"document_did": "did:fnds:c25eb417ffa90f8fedf29b385fc91f58831a470805f38474bd71f327b860f946"
            "project_id": "NewDayNewProject2020-03-05",
            "page": "inception",
            "field_index": 1
        }
    }

    print(lambda_handler(event, {}))