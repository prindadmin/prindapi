'''
This module uses the Session Token Service (STS) to create tokens for uploading
files to the S3 buckets for 1 hour
'''
import boto3
import json
import os

def lambda_handler(event, context):

    try:
        
        jwt_token = event['headers']['Authorization']

        stage_log_level = os.environ['S3_BUCKET_ARN']


        #Connect to the STS system
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
                    "Resource": ["arn:aws:s3:::como-ifc-files/" + str(cognitoID) + '/*',
                                 "arn:aws:s3:::como-ifc-files/demonstration_sites/*"]
                }
            ]
        })
        
        #Get tokens for user to assume the role
        response = client.assume_role(
            RoleArn = "arn:aws:iam::514296467270:role/webClientRole",
            Policy = policy,
            RoleSessionName = "webClientRole",
            DurationSeconds = 3600
        )
          
    except Exception as e:
        print(e)
        
        return {"Error" : "Internal server error when getting STS Token"}, 500


    return {
        "statusCode": 200,
        "body": {
            "SessionToken" : response["Credentials"]["SessionToken"],
            "Expiration" : response["Credentials"]["Expiration"].timestamp(),
            "AccessKeyId" : response["Credentials"]["AccessKeyId"], 
            "SecretAccessKey" : response["Credentials"]["SecretAccessKey"]
        }
    }
        

        
