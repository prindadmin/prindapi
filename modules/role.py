import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors


# If logger hasn't been set up by a calling function, set it here

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])


def get_all_roles():

    response = table.query(
        IndexName="GSI1", 
        KeyConditionExpression=Key("sk").eq("role-name")
    )

    try:
        items = response['Items']
    except KeyError:
        return None

    roles = []

    for item in items:

        item['roleId'] = item.pop('pk')
        item['roleName'] = item.pop('data')
        item.pop('sk')
        roles.append(item)

    return roles
