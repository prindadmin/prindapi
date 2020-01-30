import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors



# If logger hasn't been set up by a calling function, set it here
try:
    logger
except:
    from foundations.log import logger
    log.set_logging_level()

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def get_cognito_did(cognito_username):

    response = table.query(
        IndexName="GSI1",
         KeyConditionExpression=Key("sk").eq("cognitoUsername") & Key("data").eq(cognito_username)
    )
    
    try:
        did = response.get('Items')[0]['pk'][4:]
    except IndexError:
        raise errors.DIDNotFound("This username does not have a DID")
    
   
    return did