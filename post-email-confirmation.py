import boto3
import json
import os
import requests

from modules import user
from modules import auth
from modules import mail
from modules import errors

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

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

        print(event)

        username = event['request']['userAttributes']['sub']
        email_address = event['request']['userAttributes'].get('email')
        first_name = event['request']['userAttributes'].get('given_name')
        last_name = event['request']['userAttributes'].get('family_name')

        user.create_user(username, first_name=first_name, last_name=last_name, email_address=email_address)

        this_user =user.User(username)
        
        try:
            did = this_user.add_foundations_subscription()
        except errors.DIDNotFound:
            did = None

        template_data = {
            "firstName": first_name,
            "foundationsId": did
        }

        mail.send_email(email_address, "post-confirmation", template_data)

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

    return event

    

if __name__ == '__main__':

    event = {
      "version": "1",
      "region": "eu-west-1",
      "userPoolId": "eu-west-1_VL7uVkjBo",
      "userName": "6a628546-9b4e-4c43-96a4-4e30c3c37511",
      "callerContext": {
        "awsSdkVersion": "aws-sdk-unknown-unknown",
        "clientId": "1heu4dbau7agvc2nee57o65fl0"
      },
      "triggerSource": "PostConfirmation_ConfirmSignUp",
      "request": {
        "userAttributes": {
          "sub": "6a628546-9b4e-4c43-96a4-4e30c3c37511",
          "cognito:email_alias": "mr.simon.hunt+test14@gmail.com",
          "cognito:user_status": "CONFIRMED",
          "email_verified": "true",
          "email": "mr.simon.hunt+test14@gmail.com",
          "given_name": "Simon",
          "family_name": "Hunt"
        }
      },
      "response": {}
    }

    

    print(lambda_handler(event, {}))