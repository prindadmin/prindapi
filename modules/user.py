import boto3
import time
import json
import os
import requests

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors
from modules import project
from modules import auth
from modules import log
from modules import document
from modules import field

# If logger hasn"t been set up by a calling function, set it here
try:
    logger
except:
    from modules.log import logger
    log.set_logging_level()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

api_id = os.environ["FOUNDATIONS_API_ID"]
sp_did = os.environ["SP_DID"]
api_stage = os.environ["FOUNDATIONS_API_STAGE"]

class User():

    def __init__(self, username):

        # logger.info(log.function_start_output())

        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"user_{username}") & Key("sk").begins_with("userDetails_")
        )
      
        items = response['Items']
        
        if items == []:
            raise errors.UserNotFound(f"A user with name {username} was not found.")
        
        values = {}

        for item in items:    
            attribute_name = item['sk'].split('userDetails_')[1]
            values[attribute_name] = item['data']

        self.email_address = values.get('emailAddress')
        self.first_name = values.get('firstName')
        self.last_name = values.get('lastName')
        self.username = username

        logger.debug(log.function_end_output(locals()))  


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

        logger.debug(log.function_end_output(locals()))  


    def write_did(self, did):

        table.put_item(
            Item={
                "pk": f"user_{self.username}",
                "sk": "userDid",
                "data": did
            }
        )

        logger.debug(log.function_end_output(locals()))  

    def get_did_from_foundations(self):

        foundations_jwt = auth.get_foundations_jwt(sp_did)
        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/email-address/{self.email_address}/get-did"

        params = {}

        response = requests.get(
            api_url,
            data=params,
            headers={'Authorization': foundations_jwt}
        )

        response_dict = json.loads(response.content.decode('utf-8'))
      
        logger.debug(response_dict)

        try: 
            status_code = response_dict["statusCode"]
        except KeyError:
            status_code = 500

        if status_code != 200:
            print(response_dict)
            raise errors.DIDNotFound(f"A DID was not found for the email address {self.email_address}")
            
        did = response_dict["body"]["did"]

        self.write_did(did)

        logger.debug(log.function_end_output(locals()))  

        return did


    def get_projects(self):

        projects = project.get_user_projects(self.username)

        logger.debug(log.function_end_output(locals()))  

        return projects

    def get_project_invitations(self):

        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"user_{self.username}") & Key("sk").begins_with("roleInvitation_")
        )

        items = response.get("Items")
        invitations = []

        for item in items:

            item.pop("pk")
            project_id = item.pop("sk").split("roleInvitation_")[1]
            item["projectId"] = project_id
            item["roleId"] = item.pop('data')

            item["projectName"] = project.Project(project_id).project_name
            requesting_user_obj = User(item["requestedBy"])
            item["requestedByUser"] = f"{requesting_user_obj.first_name} {requesting_user_obj.last_name}"

            invitations.append(item)

        logger.debug(log.function_end_output(locals()))  

        return invitations

    def get_signature_requests(self):     

        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"user_{self.username}") 
                                 & Key("sk").begins_with("documentSignRequest_")
        )

        items = response.get('Items',[])

        print(items)

        signing_requests = []

        for item in items:
            item.pop('pk')
            s3_key = item.pop('sk').split('documentSignRequest_')[1]
            
            try:
                item['projectID'] = s3_key.split('/')[0]
                item['pageName'] = s3_key.split('/')[1]
                item['fieldID'] = s3_key.split('/')[2]
            except IndexError:
                continue

            this_field = field.Field(
                project_id=item['projectID'],
                page_name=item['pageName'],
                field_index=item['fieldID']
            )

            document_did = this_field.get_document_did()
            this_document = document.Document(document_did)
            document_version = this_document.get_version(0)

            item['filename'] = document_version.get('filename')

            requesting_user = User(item.pop('requestedBy'))
            item['requestedBy'] = {}
            item['requestedBy']['username'] = requesting_user.username
            item['requestedBy']['firstName'] = requesting_user.first_name
            item['requestedBy']['lastName'] = requesting_user.last_name

            signing_requests.append(item)

        logger.debug(log.function_end_output(locals()))  

        return signing_requests

    def get_uploaded_document_versions(self):

        documents = document.get_user_uploaded_document_versions(self.username)

        return documents


    def update(self, first_name=None, last_name=None, email_address=None):

        if first_name:
            table.put_item(
                Item={
                    "pk": f"user_{self.username}",
                    "sk": "userDetails_firstName",
                    "data": first_name
                }
            )

        if last_name:
            table.put_item(
                Item={
                    "pk": f"user_{self.username}",
                    "sk": "userDetails_lastName",
                    "data": last_name
                }
            )

        if email_address:
            table.put_item(
                Item={
                    "pk": f"user_{self.username}",
                    "sk": "userDetails_emailAddress",
                    "data": email_address
                }
            )

        logger.debug(log.function_end_output(locals()))  

    def add_foundations_subscription(
        self,
        fields=None, 
        comment=None, 
        requester_reference=None
    ):

        default_fields = [
            "firstName",
            "lastName",
            "emailAddress",
            "homePhoneNumber",
            "mobilePhoneNumber"
        ]

        if fields == None:
            fields = default_fields
            comment = "Please allow these fields for sign-up on Prin-D"

        foundations_jwt = auth.get_foundations_jwt(sp_did)

        try:
            user_did = self.get_did()
        except errors.DIDNotFound:
            try:
                user_did = self.get_did_from_foundations()
            except errors.DIDNotFound:
                # stop here and pass the exception back the caller
                raise

        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/subscription/{user_did}"

        params = {
            "requiredFields": fields,
            "comment": comment,
            "requesterReference": "Prin-D"
        }

        response = requests.post(
            api_url,
            data=params,
            headers={'Authorization': foundations_jwt}
        )

        response_dict = json.loads(response.content.decode('utf-8'))

        logger.debug("response_dict was:", response_dict)

        if response_dict["statusCode"] != 201:
            logger.debug("There was an error requesting the subscription")
        else:
            logger.debug("subscription was requested")

        logger.debug(log.function_end_output(locals()))  

        return user_did

    def get_foundations_subscription(self):

        try:
            user_did = self.get_did()
        except errors.DIDNotFound:
            return None

        foundations_jwt = auth.get_foundations_jwt(sp_did)
        
        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/subscription/{user_did}"

        params = {}

        response = requests.get(
            api_url,
            data=params,
            headers={'Authorization': foundations_jwt}
        )

        response_dict = json.loads(response.content.decode('utf-8'))

        logger.debug("response_dict was:", response_dict)

        if response_dict["statusCode"] != 200:
            logger.debug("There was an error getting the subscription")
        else:
            logger.debug("subscription API returned normally")

        logger.debug(log.function_end_output(locals()))

        subscription_details = response_dict['body']

        subscription_details['foundationsId'] = user_did  

        return subscription_details






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
                "sk": "userDetails_emailAddress",
                "data": email_address
            }
        )

    logger.debug(log.function_end_output(locals()))  

# def list_all_users():

#     response = table.query(
#         IndexName="GSI1", 
#         KeyConditionExpression=Key("sk").eq("userDetails")
#     )

#     items = response['Items']


#     users = []

#     for item in items:
#         print('item')
#         item['username'] = item.pop('pk').split('user_')[1]
#         item.pop('sk')
#         item['name'] = item.pop('data')
        
#         users.append(item)

#     return users


