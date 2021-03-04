# import unittest
import time
import boto3
import os
import json
import io
import zipfile
from moto import mock_dynamodb2
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj)
        return super(DecimalEncoder, self).default(obj)

current_directory = os.path.dirname(os.path.realpath(__file__))

environment = {
        "TABLE_NAME": "prind-unittest",
        "AWS_REGION": "eu-west-1",
        "FOUNDATIONS_API_ID": "xxxxxx",
        "FOUNDATIONS_API_STAGE": "test",
        "SP_DID": "did:fnds:ca7722fabb7009aecf997a59973cd4fc810b820b15fd041b7671f146e97dcfc1",
        "FACTOM_EXPLORER_URL": "https://testnet.explorer.factom.pro/entries/{entry_hash}",
        "S3_BUCKET_NAME": "test_bucket",
        "S3_BUCKET_ARN": "arn:aws:s3:::test_bucket",
        "S3_USER_PROFILES_BUCKET_ARN": "arn:aws:s3:::test_bucket-profiles",
        "AWS_ACCESS_KEY_ID": "AKIAIOSFODNN7EXAMPLE",
        "AWS_SECRET_ACCESS_KEY": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
    }
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

def create_bucket_with_versioning(bucket_name):

        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        bucket.create(ACL="public-read", CreateBucketConfiguration={"LocationConstraint": "us-west-1"})
        bucket.Versioning().enable()

        return bucket

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

def database_snapshot(table, gsi=False):
    
    scan_kwargs={}
    
    if gsi:
        scan_kwargs['IndexName']='GSI1'

    response = table.scan(**scan_kwargs)

    return json.dumps(response.get('Items'), cls=DecimalEncoder)

