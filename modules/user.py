import boto3
import time
import json
import os
import requests
from datetime import datetime

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
      
        if response_dict.get("statusCode") != 200:
            logger.error(f"error calling /sp/email-address/{self.email_address}/get-did: {response_dict}")
            raise errors.DIDNotFound(f"A DID was not found for the email address {self.email_address}")
            
        logger.info(f"response from /sp/email-address/{self.email_address}/get-did is {response_dict}")

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
            this_project = project.Project(project_id)

            if not this_project.active:
                continue

            item["projectId"] = project_id
            item["roleId"] = item.pop('data')

            item["projectName"] = this_project.project_name
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

        signing_requests = []

        user_object = {}
        project_object = {}
        document_version_object = {}
        field_object = {}

        for item in items:
            item.pop('pk')
            s3_key = item.pop('sk').split('documentSignRequest_')[1]
            
            try:
                item['projectID'] = s3_key.split('/')[0]
                item['pageName'] = s3_key.split('/')[1]
                item['fieldID'] = s3_key.split('/')[2]
            except IndexError:
                logger.error(f"project/page/field was not properly defined in the s3_key, so skipping s3_key: {s3_key}")
                continue

            project_id = item['projectID']
            page_name = item['pageName']
            field_index = item['fieldID']

            # project information
            try:
                project_object[project_id]
            except KeyError:
                project_object[project_id] = project.Project(project_id=item['projectID'])

            if not project_object[project_id].active:
                logger.info(f"project {project_id} is not active; skipping request")
                continue

            item['projectName'] = project_object[project_id].project_name

            # user information
            requesting_username = item.pop('requestedBy')
            item['requestedBy'] = {}
            item['requestedBy']['username'] = requesting_username
            item['requestedBy']['firstName'] = item.get('requesterFirstName')
            item['requestedBy']['lastName'] = item.get('requesterLastName')

            # document information
            try:
                document_version_object[f"{project_id}/{page_name}/{field_index}"]
            except KeyError:
                logger.info("document version object was not already defined, so creating it")

                document_version_object[f"{project_id}/{page_name}/{field_index}"] = document.Document(
                    project_id=item['projectID'], 
                    page=item['pageName'], 
                    field_index=item['fieldID']
                ).get_version(0)

            item['filename'] = document_version_object[f"{project_id}/{page_name}/{field_index}"].get('filename')

            # field information  
            item['fieldTitle'] = item.get('fieldTitle')

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

        logger.info(f"api_url is: {api_url}")

        params = {
            "requiredFields": fields,
            "comment": comment,
            "requesterReference": "Prin-D"
        }

        logger.info(f"params are: {params}")

        response = requests.post(
            api_url,
            data=json.dumps(params),
            headers={'Authorization': foundations_jwt}
        )

        response_dict = json.loads(response.content.decode('utf-8'))

        if response_dict.get("statusCode") != 201:
            logger.error(f"error calling /sp/subscription/{user_did}: {response_dict}")
        else:
            logger.info(f"response from /sp/subscription/{user_did} is {response_dict}")

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

        if response_dict.get("statusCode") != 200:
            logger.error(f"error calling /sp/subscription/{user_did} is {response_dict}")
            subscription_details = None
        else:
            logger.info(f"response from /sp/subscription/{user_did} is {response_dict}")
            subscription_details = response_dict['body']
            subscription_details['foundationsId'] = user_did

        logger.debug(log.function_end_output(locals()))

        return subscription_details

    def add_signed_document(self, document_did, document_version, signed_at, entry_hash):

        document_details = document.get_document_field(document_did)
        
        project_id = document_details['projectId']
        page = document_details['page']
        field = document_details['field']
        
        table.put_item(
            Item={
                "pk": f"user_{self.username}",
                "sk": f"signedDocument_{project_id}/{page}/{field}_v{document_version}",
                "data": datetime.utcnow().isoformat(),
                "signedAt": signed_at,
                "entryHash": entry_hash
            }
        )

    def get_signed_documents(self):

        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"user_{self.username}") & Key("sk").begins_with("signedDocument_")
        )

        items = response['Items']

        signed_documents = []

        for item in items:
            field_string = item['sk'].split("_")[1]
            item['projectID'] = field_string.split('/')[0]
            item['pageName'] = field_string.split('/')[1]
            item['fieldID'] = field_string.split('/')[2]

            this_project = project.Project(item['projectID'])

            if not this_project.active:
                continue

            this_field = field.Field(
                field_index=item['fieldID'],
                page_name=item['pageName'], 
                project_id=item['projectID'] 
            )

            item['fieldTitle'] = this_field.get()['title']

            item['signedAt'] = datetime.utcfromtimestamp(item['signedAt']).isoformat()

            item.pop('pk')
            item.pop('sk')
            item.pop('data')

            signed_documents.append(item)

        return signed_documents




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

