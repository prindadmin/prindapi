import boto3
import json
import os
import requests

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

from modules import user
from modules import auth

def lambda_handler(event, context):

    try:

        print(event)

        username = event['request']['userAttributes']['sub']
        email_address = event['request']['userAttributes'].get('email')
        first_name = event['request']['userAttributes'].get('given_name')
        last_name = event['request']['userAttributes'].get('family_name')

        user.create_user(username, first_name=first_name, last_name=last_name, email_address=email_address)

        api_id = os.environ["FOUNDATIONS_API_ID"]
        sp_did = os.environ["SP_DID"]
        api_stage = os.environ["FOUNDATIONS_API_STAGE"]

        foundations_jwt = auth.get_foundations_jwt(sp_did)
        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/email-address/{email_address}/get-did"

        params = {
        }

        response = requests.get(
            api_url,
            data=params,
            headers={'Authorization': foundations_jwt}
        )

        response_dict = json.loads(response.content.decode('utf-8'))

        print(response.status_code)

        if not response_dict['statusCode'] == 200:
            
            print("status code was", response.status_code)
            print("response content was", response_dict)

        else:
            
            print(response_dict)
            did = response_dict['body']['did']
            print(did)

            this_user =user.User(username)
            this_user.write_did(did)

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
      "userName": "c9b5377d-8503-452a-8d3a-76f734f97c6c",
      "callerContext": {
        "awsSdkVersion": "aws-sdk-unknown-unknown",
        "clientId": "1heu4dbau7agvc2nee57o65fl0"
      },
      "triggerSource": "PostConfirmation_ConfirmSignUp",
      "request": {
        "userAttributes": {
          "sub": "c9b5377d-8503-452a-8d3a-76f734f97c6c",
          "cognito:email_alias": "mr.simon.hunt+test6@gmail.com",
          "cognito:user_status": "CONFIRMED",
          "email_verified": "true",
          "email": "mr.simon.hunt+test6@gmail.com",
          "given_name": "Simon",
          "family_name": "Hunt"
        }
      },
      "response": {}
    }

    

    print(lambda_handler(event, {}))