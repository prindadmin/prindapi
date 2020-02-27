import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors
from modules import page
from modules import log

# If logger hasn"t been set up by a calling function, set it here
try:
    logger
except:
    from modules.log import logger
    log.set_logging_level()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

class Field(page.Page):

    def __init__(self, field_index, page_name, project_id):

        page.Page.__init__(self, page=page_name, project_id=project_id)

        self.page_name = page_name
        self.project_id = project_id
        self.field_index = field_index

        logger.debug(log.function_end_output(locals()))

    def get_document_did(self):

        response = table.get_item(
            Key={
                "pk": f"project_{self.project_id}",
                "sk": f"field_{self.page_name}_{self.field_index}"
            }
        )


        item = response.get('Item')
        document_did = None

        if item:
            if item['type'] == 'file':           
                if item.get('fieldDetails'):
                    document_did = item['fieldDetails'].get('documentDid')

        if not document_did:
            raise errors.DocumentNotFound(f"The field {self.project_id}/{self.page_name}/{self.field_index} not have a document DID")

        logger.debug(log.function_end_output(locals()))  

        return document_did



            








