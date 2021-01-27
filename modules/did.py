import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors
from modules import log

# If logger hasn"t been set up by a calling function, set it here
try:
    logger
except:
    from modules.log import logger
    log.set_logging_level()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


class Did():

    def __init__(self, did):

        self.did = did

    def get_cognito_username(self):

        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("sk").eq("userDid")&Key("data").eq(self.did)
        )

        try:
            cognito_username = response.get("Items")[0]["pk"].split('_')[1]
        except (TypeError, KeyError, IndexError):
            raise errors.DIDNotFound(f"There is no cognito username for the {self.did}")

        logger.debug(log.function_end_output(locals()))  

        return cognito_username

