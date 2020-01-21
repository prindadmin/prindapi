'''
This module uses the Session Token Service (STS) to create tokens for uploading
files to the S3 buckets for 1 hour
'''
import boto3
import json
import os


def get_cognito_username(token):

    decoded = jwt.decode(token, verify=False)['cognito:username']
    
 
    return decoded['cognito:username']


def lambda_handler(event, context):

    # try:
        
    # "cognitoPoolClaims": {
    #     "sub": "81de030e-7a68-4426-9c12-160fca975a92"
    # },

    jwt_token = event['headers']['Authorization']
    cognito_username = event['cognitoPoolClaims']['sub']
    s3_bucket_arn = os.environ['S3_BUCKET_ARN']

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
                "Resource": [f"{s3_bucket_arn}/{cognito_username}/*",
                            f"{s3_bucket_arn}/demonstration_sites/*"]
            }
        ]
    })
    
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
    
    return {
        "statusCode": 200,
        "body": {
            "SessionToken" : response["Credentials"]["SessionToken"],
            "Expiration" : response["Credentials"]["Expiration"].timestamp(),
            "AccessKeyId" : response["Credentials"]["AccessKeyId"], 
            "SecretAccessKey" : response["Credentials"]["SecretAccessKey"]
        }
    }
        

        
