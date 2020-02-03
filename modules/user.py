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


class User():

    def __init__(self, username):

        # logger.info(log.function_start_output())

        response = table.get_item(
            Key={
                "pk": f"user_{username}",
                "sk": "user-name"
            }
        )

        try:
            item = response['Item']
        except KeyError:
            raise UserNotFound(f"A user with name {username} was not found.")
        
        self.username = username
        self.name = item['data']

    def get_did(self):

        response = table.get_item(
             Key={
                "pk": f"user_{self.username}",
                "sk": "did"
            }
        )
        
        try:
            did = response.get("Item")["data"]
        except (TypeError, KeyError):
            raise errors.DIDNotFound("This username does not have a DID")
        
        return did


    def write_did(self, did):

        table.put_item(
            Item={
                "pk": f"user_{self.username}",
                "sk": "did",
                "data": did
            }
        )


def create_user(username, name):


    table.put_item(
        Item={
            "pk": f"user_{username}",
            "sk": "user-name",
            "data": name
        }
    )

def list_all_users():

    response = table.query(
        IndexName="GSI1", 
        KeyConditionExpression=Key("sk").eq("user-name")
    )

    try:
        items = response['Items']
    except KeyError:
        items = []

    users = []

    for item in items:
        print('item')
        item['username'] = item.pop('pk').split('user_')[1]
        item.pop('sk')
        item['name'] = item.pop('data')
        
        users.append(item)

    return users


