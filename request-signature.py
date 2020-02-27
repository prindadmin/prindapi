import boto3
import os
import time

from modules import errors
from modules import document
from modules import user
from modules import mail
from modules import field

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

        requesting_user = user.User(event['cognitoPoolClaims']['sub'])
        signing_user = user.User(event['body']['signingUsername'])

        this_field = field.Field(
            field_index=int(event['path']['field_index']),
            page_name=event['path']['page'],
            project_id=event['path']['project_id']
        )

        document_did = this_field.get_document_did()
 
        table.put_item(
            Item={    
                "pk": f"user_{signing_user.username}",
                "sk": f"documentSignRequest_{document_did}",
                "requestedBy": requesting_user.username,
                "requestedAt": str(int(time.time()))
            }
        )

        template_data = {
            "firstName": requesting_user.first_name,
            "lastName": requesting_user.last_name
        }

        mail.send_email(signing_user.email_address, "document-signature-request", template_data)

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
            #"sub": "778bd486-4684-482b-9565-1c2a51367b8c"
            "sub": "a9fa394f-ed94-444c-84fe-6821f538ddd9"
        },
        "path": {
            "project_id": "ProjectNumberSix",
            "page": "inception",
            "field_index": "1"
        },
        "body": {
            #"signingUsername": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa"
            "signingUsername": "f9c255cb-a42b-4359-a8bd-2ebec5dfa2fa"
        }
    }

    lambda_handler(event, {})