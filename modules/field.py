import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors
# from modules import page
from modules import log

# If logger hasn"t been set up by a calling function, set it here
try:
    logger
except:
    from modules.log import logger
    log.set_logging_level()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

class Field():

    def __init__(self, field_index, page_name, project_id):

        self.page_name = page_name
        self.project_id = project_id
        self.field_index = field_index

        logger.debug(log.function_end_output(locals()))

    def get(self):

        response = table.get_item(
            Key={
                "pk": f"project_{self.project_id}",
                "sk": f"field_{self.page_name}_{self.field_index}"
            }
        )

        populated_field = response.get('Item')

        #print("populated field", populated_field)

        if not populated_field:
            response = table.get_item(
                Key={
                    "pk": f"defaultField_{self.page_name}",
                    "sk": f"fieldIndex_{self.field_index}"
                }
            )

            try:
                default_field = response['Item']
                return_field = default_field
            except KeyError:
                raise errors.FieldNotFound(f"No field was found for {self.project_id}/{self.page_name}/{self.field_index}")

        else:
            return_field = populated_field

        return_field.pop('pk')
        return_field.pop('sk')

        return return_field

    def get_document_did(self):

        item = self.get()
        
        document_did = None

        if item:
            if item['type'] == 'file':           
                if item.get('fieldDetails'):
                    document_did = item['fieldDetails'].get('documentDid')

        if not document_did:
            raise errors.DocumentNotFound(f"The field {self.project_id}/{self.page_name}/{self.field_index} not have a document DID")

        logger.debug(log.function_end_output(locals()))  

        return document_did









            








