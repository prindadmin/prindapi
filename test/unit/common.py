# import unittest
import time
import boto3
import os
import json
import io
import zipfile
from moto import mock_dynamodb2
from boto3.dynamodb.conditions import Key, Attr

current_directory = os.path.dirname(os.path.realpath(__file__))

def create_table():

    dynamodb = boto3.resource('dynamodb', os.environ['AWS_REGION'])
    table_name = os.environ['TABLE_NAME']

    print('creating table', table_name)

    table = dynamodb.create_table(
        TableName=table_name,
        KeySchema=[
            {
                'AttributeName': 'pk',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': 'sk',
                'KeyType': 'RANGE'
            },
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'pk',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'sk',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'data',
                'AttributeType': 'S'
            },

        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        },
        GlobalSecondaryIndexes=[
            {
                'IndexName': 'GSI1',
                'KeySchema': [
                    {
                        'AttributeName': 'sk',
                        'KeyType': 'HASH'
                    },
                    {
                        'AttributeName': 'data',
                        'KeyType': 'RANGE'
                    }
                ],
                'Projection': {
                    'ProjectionType': 'ALL'
                },
                'ProvisionedThroughput': {
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            }
        ]
    )

    return table

def import_json_records_file(file_name, table):

    items_file = open("{}/json-data/dynamodb/{}".format(current_directory, file_name))
    
    items =  json.loads(items_file.read())

    items_file.close()

    put_items(items, table)
       

def put_items(items_list, table):
    
    for item in items_list:
        table.put_item(
            Item=  item
        )

