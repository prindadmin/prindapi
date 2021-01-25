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

def get_foundations_jwt(did):
    """
    called by function that needs to call Foundation to get an auth token
    """
    response = table.get_item(
        Key={
            "pk": "apiKey_foundations",
            "sk": did
        }
    )

    try:
        api_key = response.get("Item")["apiKey"]
        expiry_time = response.get("Item")["expiryTimestamp"]

    except (TypeError, KeyError):
        api_key = update_foundations_jwt(did)
        return api_key

    # create a new JWT if this JWT expires in less than 5 mins
    seconds_remaining = int(expiry_time) - time.time()
    
    if seconds_remaining < 300:
        logger.debug(f"seconds remaining {seconds_remaining}")
        api_key = update_foundations_jwt(did) 

    logger.debug(log.function_end_output(locals()))   

    return api_key


def update_foundations_jwt(did):
    """
    called by get_jwt() if the token has expired or is near to expiry

    This will generate another JWT using the private key, which will be
    stored in the database for now
    """ 
    import jwt

    private_key = get_private_key(did)

    expiry_time = int(time.time()) + 3600

    created_jwt = jwt.encode({'did': did, 'exp' : expiry_time}, private_key, algorithm='RS256').decode('utf-8')

    response = table.put_item(
         Item={
            "pk": "apiKey_foundations",
            "sk": did,
            "apiKey": created_jwt,
            "expiryTimestamp": expiry_time
        }
    )

    logger.debug(log.function_end_output(locals()))

    return created_jwt


def get_private_key(did):

    response = table.get_item(
         Key={
            "pk": "privateKey",
            "sk": did
        }
    )

    try:
        private_key = response.get("Item")["key"]
    except (TypeError, KeyError):
        raise errors.DIDNotFound("There is no private key for this DID")

    logger.debug(log.function_end_output(locals()))  

    return private_key


 
