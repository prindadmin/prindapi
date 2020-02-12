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

        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"user_{username}") & Key("sk").begins_with("userDetails_")
        )

        try:
            items = response['Items']
        except KeyError:
            raise errors.UserNotFound(f"A user with name {username} was not found.")
        
        values = {}

        for item in items:    
            attribute_name = item['sk'].split('userDetails_')[1]
            values[attribute_name] = item['data']

        self.email_address = values.get('emailAddress')
        self.first_name = values.get('firstName')
        self.last_name = values.get('lastName')
        self.username = username


    def get_did(self):

        response = table.get_item(
             Key={
                "pk": f"user_{self.username}",
                "sk": "userDid"
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
                "sk": "userDid",
                "data": did
            }
        )


def create_user(username, first_name=None, last_name=None, email_address=None):

    if first_name:
        table.put_item(
            Item={
                "pk": f"user_{username}",
                "sk": "userDetails_firstName",
                "data": first_name
            }
        )

    if last_name:
        table.put_item(
            Item={
                "pk": f"user_{username}",
                "sk": "userDetails_lastName",
                "data": last_name
            }
        )

    if email_address:
        table.put_item(
            Item={
                "pk": f"user_{username}",
                "sk": "userDetails_lastName",
                "data": email_address
            }
        )

# def list_all_users():

#     response = table.query(
#         IndexName="GSI1", 
#         KeyConditionExpression=Key("sk").eq("userDetails")
#     )

#     try:
#         items = response['Items']
#     except KeyError:
#         items = []

#     users = []

#     for item in items:
#         print('item')
#         item['username'] = item.pop('pk').split('user_')[1]
#         item.pop('sk')
#         item['name'] = item.pop('data')
        
#         users.append(item)

#     return users


