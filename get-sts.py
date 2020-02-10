'''
This module uses the Session Token Service (STS) to create tokens for uploading
files to the S3 buckets for 1 hour
'''
import boto3
import json
import os

from modules import page


def get_cognito_username(token):

    decoded = jwt.decode(token, verify=False)['cognito:username']
    
 
    return decoded['cognito:username']


def lambda_handler(event, context):

    #jwt_token = event['headers']['Authorization']
    cognito_username = event['cognitoPoolClaims']['sub']
    s3_bucket_arn = os.environ['S3_BUCKET_ARN']

    print(cognito_username)

    # #Connect to the STS system
    client = boto3.client('sts')

    project_id = event['path']['project_id']
    page_name = event['path']['page']

    this_page = page.Page(page_name, project_id)

    if not this_page.user_has_permission(cognito_username):
        raise InsufficientPermission('User does not have permission to this project')

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

    print(policy)
    
    #Get tokens for user to assume the role
    response = client.assume_role(
        RoleArn = "arn:aws:iam::434494845257:role/webClientRole",
        Policy = policy,
        RoleSessionName = "webClientRole",
        DurationSeconds = 3600
    )
          
    # except Exception as e:
    #     print(e)
        
    #     return {"Error" : "Internal server error when getting STS Token"}, 500

    # return {
    #     "cognitoUsername": cognito_username,
    #     "s3BucketArn": s3_bucket_arn
    # }

    return_dict = {
        "SessionToken" : response["Credentials"]["SessionToken"],
        "Expiration" : response["Credentials"]["Expiration"].timestamp(),
        "AccessKeyId" : response["Credentials"]["AccessKeyId"], 
        "SecretAccessKey" : response["Credentials"]["SecretAccessKey"]
    }

    print(
        f'export AWS_ACCESS_KEY_ID={response["Credentials"]["AccessKeyId"]}\n'
        f'export AWS_SECRET_ACCESS_KEY={response["Credentials"]["SecretAccessKey"]}\n'
        f'export AWS_SESSION_TOKEN={response["Credentials"]["SessionToken"]}\n'
    )

    return {
        "statusCode": 200,
        "body": return_dict
    }


if __name__ == '__main__':

    event = {
        "path": {
            "project_id": "ProjectNumberFour",
            "page": "feasibility",
        },
        "cognitoPoolClaims": {
            "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
    }
    }

    lambda_handler(event, {})
        

