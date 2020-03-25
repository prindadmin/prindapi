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

        email_address = event['request']['userAttributes'].get('email')

        if event['triggerSource'] == "PostConfirmation_ConfirmSignUp":
            
            username = event['request']['userAttributes']['sub']
            first_name = event['request']['userAttributes'].get('given_name')
            last_name = event['request']['userAttributes'].get('family_name')

            user.create_user(username, first_name=first_name, last_name=last_name, email_address=email_address)

            this_user = user.User(username)

            try:
                did = this_user.add_foundations_subscription()
            except errors.DIDNotFound:
                did = None

            # get any project invitations against this email address
            response = table.query(
                KeyConditionExpression=Key("pk").eq(f"emailAddress_{email_address}") & Key("sk").begins_with("roleInvitation_")
            )

            email_invites = response.get("Items")

            # put those invitations under the user account
            for email_invite in email_invites:
              
                email_invite_key = {
                    'pk': email_invite['pk'],
                    'sk': email_invite['sk']
                }

                logger.info(f"deleting email invite {email_invite_key}" )

                table.delete_item(
                    Key=email_invite_key
                )

                user_invite = email_invite.copy()

                user_invite['pk'] = f"user_{username}"
                user_invite['inviteeFirstName'] = first_name
                user_invite['inviteeLastName'] = last_name

                logger.info(f"adding user invite {user_invite}")
                
                table.put_item(
                    Item=user_invite
                )

            template_data = {
                "firstName": first_name,
                "foundationsId": did
            }

            mail.send_email(email_address, "post-confirmation", template_data)

        elif event['triggerSource'] == "PostConfirmation_ConfirmForgotPassword":

            template_data = {}

            mail.send_email(email_address, "post-confirmation-forgot-password", template_data)

    # catch any application errors
    except errors.ApplicationError as error:
        return {
            'statusCode': 400,
            "Error": error.get_error_dict()
        }
    # catch unhandled exceptions
    except Exception as e:
        
        # logger.error(log.logging.exception("message"))

        return {
            'statusCode': 500,
            'Error': errors.UnhandledException(context.log_group_name, context.log_stream_name, context.aws_request_id).get_error_dict()
        }

    return event

    

if __name__ == '__main__':

    event = {
      "sign-up": {'version': '1', 'region': 'eu-west-1', 'userPoolId': 'eu-west-1_VL7uVkjBo', 'userName': 'cee1a188-7a4b-48fc-b4b1-5b9adbcf43cb', 'callerContext': {'awsSdkVersion': 'aws-sdk-unknown-unknown', 'clientId': 'fbss4knsc8gmgct526ci8kp3a'}, 'triggerSource': 'PostConfirmation_ConfirmSignUp', 'request': {'userAttributes': {'sub': 'cee1a188-7a4b-48fc-b4b1-5b9adbcf43cb', 'cognito:email_alias': 'mr.simon.hunt+test29@gmail.com', 'cognito:user_status': 'CONFIRMED', 'email_verified': 'true', 'given_name': 'Simon', 'family_name': 'Hunt', 'email': 'mr.simon.hunt+test29@gmail.com'}}, 'response': {}},
      "forgot-password": {
        "version": "1",
        "region": "eu-west-1",
        "userPoolId": "eu-west-1_VL7uVkjBo",
        "userName": "4a9d66e8-f725-4c24-be3d-d3bdd417cb08",
        "callerContext": {
          "awsSdkVersion": "aws-sdk-unknown-unknown",
          "clientId": "1heu4dbau7agvc2nee57o65fl0"
        },
        "triggerSource": "PostConfirmation_ConfirmForgotPassword",
        "request": {
          "userAttributes": {
            "sub": "4a9d66e8-f725-4c24-be3d-d3bdd417cb08",
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
    }

    

    print(lambda_handler(event["sign-up"], {}))