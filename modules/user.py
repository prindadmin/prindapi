import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors



# If logger hasn"t been set up by a calling function, set it here

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def get_did(cognito_username):

    response = table.get_item(
         Key={
            "pk": f"user_{cognito_username}",
            "sk": "did"
        }
    )
    
    try:
        did = response.get("Item")["data"]
    except (TypeError, KeyError):
        raise errors.DIDNotFound("This username does not have a DID")
    
   
    return did


def write_did(cognito_username, did):

    table.put_item(
        Item={
            "pk": f"user_{cognito_username}",
            "sk": "did",
            "data": did
        }
    )

def get_cognito_username(did):

    response = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("sk").eq("did")&Key("data").eq(did)
    )

    try:
        cognito_username = response.get("Items")[0]["pk"].split('_')[1]
    except (TypeError, KeyError, IndexError):
        raise errors.DIDNotFound("The DID given is not in the database")

    return cognito_username
