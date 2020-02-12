'''
This module uses the Session Token Service (STS) to create tokens for uploading
files to the S3 buckets for 1 hour
'''
import boto3

from modules import user


def lambda_handler(event, context):

    #jwt_token = event['headers']['Authorization']
    cognito_username = event['cognitoPoolClaims']['sub']

    this_user = user.User(cognito_username)

    projects = this_user.get_projects()
         
    return {
        "statusCode": 200,
        "body": projects
    }


if __name__ == '__main__':

    event = {
        "cognitoPoolClaims": {
            "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
        }
    }

    print(lambda_handler(event, {}))
        

