import boto3
import time
import json
import os
import requests

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

if not os.getenv("RUNNING_ON_AWS"):
    print("not running on AWS, so loading environment")
    from dotenv import load_dotenv

    load_dotenv()

env = os.environ["ENVIRONMENT_NAME"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])
ssm = boto3.client("ssm")

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


class ProcoreAuth():

    client_id = os.environ.get('PROCORE_CLIENT_ID')

    @classmethod
    def get_client_secret(cls):
        """
        gets the client_id and client_secret for the Procore Authentication endpoints
        """

        response = ssm.get_parameter(
            Name=f"/prind-api/procore-client-secret/{env}", WithDecryption=True
        )

        try:
            client_secret = response["Parameter"]["Value"]
        except (TypeError, KeyError) as parameter_not_found:
            raise Exception(
                "clent_secret parameter not found in parameter store"
            ) from parameter_not_found

        return client_secret

    @classmethod
    def refresh_access_token(cls, refresh_token):
        return cls.request_access_token(refresh_token=refresh_token)

    @classmethod
    def request_access_token_with_auth_code(cls, auth_code, request_uri):
        return cls.request_access_token(auth_code=auth_code, request_uri=request_uri)

    @classmethod
    def request_access_token(cls, refresh_token=None, auth_code=None, request_uri=None):
        """
        gets access token if 'auth_code' is supplied, 
        or refreshes it if refresh_token is supplied
        """

        grant_type = 'refresh_token' if refresh_token else 'authorization_code'

        base_url = os.environ['PROCORE_AUTH_BASE_URL']

        params = {
            "grant_type": grant_type,
            "client_id": cls.client_id,
            "client_secret": cls.get_client_secret(),
            "redirect_uri": request_uri
        }

        if grant_type == 'refresh_token':
            params['refresh_token'] = refresh_token
        else:
            params['code'] = auth_code
        
        response = requests.post(f'{base_url}/oauth/token', params)

        if not response.ok:
            logger.error(response.json())
            raise errors.InvalidProcoreAuth('Could not authenticate with procore')

        return response.json()

    @classmethod
    def store_auth_token(cls, cognito_username, response):

        print(response)

        access_token = response['access_token']
        refresh_token = response['refresh_token']
        created_at =  response['created_at']
        lifetime =  response['expires_in']
        expires_at = created_at + lifetime

        ProcoreAuthItem.put(
            cognito_username,
            access_token,
            refresh_token,
            created_at,
            expires_at,
            lifetime
        )

    @classmethod
    def retrieve_auth_token(cls, cognito_username):

        try:
            item = ProcoreAuthItem.get(cognito_username)
        except errors.ItemNotFound:
            raise errors.InvalidProcoreAuth(f'No auth token was found for username {cognito_username}')

        return item

    @classmethod
    def valid_access_token(cls, cognito_username):
        """
        Refreshes the access token if required and returns true
        if sucessful
        """
        item = cls.retrieve_auth_token(cognito_username)

        if int(item['expiresAt']) < time.time():
            item = cls.refresh_access_token(item['refreshToken'])
            cls.store_auth_token(cognito_username, item)

        return True

class ProcoreAuthItem():

    @classmethod
    def item(
        cls,
        cognito_username,
        access_token,
        refresh_token,
        created_at,
        expires_at,
        lifetime
    ):

        item = {
            "pk": f"user#{cognito_username}",
            "sk": "procoreAuthentication",
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "createdAt": str(created_at),
            "expiresAt": str(expires_at),
            "lifetime": str(lifetime),
        }

        return item

    @classmethod
    def put(
        cls,
        cognito_username,
        access_token,
        refresh_token,
        created_at,
        expires_at,
        lifetime
    ):

        item = cls.item(
            cognito_username,
            access_token,
            refresh_token,
            created_at,
            expires_at,
            lifetime
        )

        table.put_item(
            Item=item
        )

    @classmethod
    def get(
        cls,
        cognito_username
    ):

        response = table.get_item(Key={
            "pk": f"user#{cognito_username}",
            "sk": "procoreAuthentication"
        })
        
        item = response.get('Item')

        if not item:
            raise errors.ItemNotFound('Item with specified key does not exist')

        return item



 
