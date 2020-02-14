import boto3
import os
import time
import requests

from modules import errors
from modules import document
from modules import user
from modules import auth

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):

    try:

        this_user = user.User(event['cognitoPoolClaims']['sub'])

        api_id = os.environ["FOUNDATIONS_API_ID"]
        sp_did = os.environ["SP_DID"]
        api_stage = os.environ["FOUNDATIONS_API_STAGE"]

        foundations_jwt = auth.get_foundations_jwt(sp_did)

        document_obj = document.Document(event['path']['document_did'])
        document_version = 0 # latest

        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{document_obj.document_did}/signing-request/{document_version}"

        params = {
            "signingDid": this_user.get_did()
        }

        print(params)

        response = requests.post(
            api_url,
            data=params,
            headers={'Authorization': foundations_jwt}
        )

        if not response.status_code == 201:
            
            print("status code was", response.status_code)
            print("response content was", response_dict)
            
            raise Exception('API call failed')
  
        table.delete_item(
            Key={    
                "pk": f"user_{this_user.username}",
                "sk": f"documentSignRequest_{document_obj.document_did}",
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
        "cognitoPoolClaims": {
            "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
            #"sub": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa"
        },
        "path": {
            "document_did": "did:fnds:c25eb417ffa90f8fedf29b385fc91f58831a470805f38474bd71f327b860f946"
        }
    }

    print(lambda_handler(event, {}))