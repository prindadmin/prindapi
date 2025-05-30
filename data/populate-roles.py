import boto3
import json
import os

stage = input("enter stage: ")

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(f'prind-{stage}')

current_directory = os.path.dirname(os.path.realpath(__file__))


role_list = open("{}/roles.json".format(current_directory)).read()

role_list = json.loads(role_list)

for role in role_list:

    table.put_item(
        Item=role
    )