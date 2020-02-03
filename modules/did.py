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
