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

class Document():

    def __init__(self, document_did):

        # logger.info(log.function_start_output())

        response = table.get_item(
            Key={
                "pk": f"document_{document_did}",
                "sk": "document"
            }
        )

        try:
            item = response['Item']
        except KeyError:
            raise errors.DocumentNotFound(f"A document with DID {document_did} was not found.")

        
        s3BucketName, s3Key, filename, versionNumber 

        self.document_did = document_did
        self.s3_bucket_name = item['s3BucketName']
        self.s3_key = item['s3Key']
        self.filename = item['filename']
        self.versionNumber = item['versionNumber']


if __name__ == "__main__":

    pass
    
    #get_project("TestProject")
    #create_project("Test Project", "This is a test project", "West Street, Farnham, Surrey")



