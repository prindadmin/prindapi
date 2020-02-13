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

class Role():

    def __init__(self, role_id):

        # logger.info(log.function_start_output())

        response = table.get_item(
            Key={
                "pk": f"role_{role_id}",
                "sk": "role-name"
            }
        )

        try:
            item = response['Item']
        except KeyError:
            raise RoleNotFound(f"A role with ID {role_id} was not found.")

        self.role_id = role_id
        self.role_name = item['data']


def list_all_roles():

    response = table.query(
        IndexName="GSI1", 
        KeyConditionExpression=Key("sk").eq("role-name")
    )

    items = response['Items']


    roles = []

    for item in items:

        item['roleId'] = item.pop('pk')
        item['roleName'] = item.pop('data')
        item.pop('sk')
        roles.append(item)

    return roles


