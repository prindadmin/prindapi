import boto3
import time
import json
import os
import requests
from datetime import datetime

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors
from modules import auth
from modules import user
from modules import did
from modules import log


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
factom_explorer_domain = os.environ["FACTOM_EXPLORER_DOMAIN"]

foundations_jwt = auth.get_foundations_jwt(sp_did)

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
            raise errors.DocumentNotFound(f"A document with DID {self.document_did} was not found.")

        self.document_did = document_did
        self.s3_bucket_name = item['s3BucketName']
        self.s3_key = item['s3Key']
        self.filename = None

        logger.debug(log.function_end_output(locals()))  

    def get_version(self, version):

        response = table.get_item(
            Key={
                "pk": f"document_v{version}_{self.document_did}",
                "sk": "documentVersion"
            }
        )

        try:
            item = response['Item']
        except KeyError:
            raise errors.DocumentVersionNotFound(f"Version {version} of document DID {self.document_did} does not exist")

        item.pop('pk')
        item.pop('sk')

        # use the value in 'data' for uploadedBy 
        # if it exists
        try:
            item['uploadedBy'] = item.pop('data').split('_')[1]
        except KeyError:
            pass

        logger.debug(log.function_end_output(locals()))  

        return item

    def get_current_version_number(self):

        version = self.get_version(0)  

        return int(version['versionNumber'])

    def get_foundations_info(self):

        foundations_jwt = auth.get_foundations_jwt(sp_did)

        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{self.document_did}/versions"

        params = {}

        response = requests.get(
            api_url,
            params=params,
            headers={'Authorization': foundations_jwt}
        )

        print(f"response from /sp/document-did/document_did/versions is", response.content.decode('utf-8'))

        versions = json.loads(response.content.decode('utf-8')).get('body', {})

        logger.debug(log.function_end_output(locals()))  

        return versions

    def get_version_signatures(self, version):

        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{self.document_did}/version-signatures/{version}"

        params = {}

        response = requests.get(
            api_url,
            params=params,
            headers={'Authorization': foundations_jwt}
        )

        signatures = json.loads(response.content.decode('utf-8'))['body']

        logger.debug(log.function_end_output(locals()))  

        return signatures

    def get_all_info(self):

        foundations_document = self.get_foundations_info()

        versions = foundations_document['documentVersions']

        latest_version = len(versions) - 1

        latest_version_signatures = self.get_version_signatures(latest_version)['signatures']

        for signing in latest_version_signatures:

            signing['signedBy'] = signing.pop('signingDid')
 
            try:     
                signing_username = did.Did(signing['signedBy']).get_cognito_username()
            except errors.DIDNotFound:
                signing_username = 'Unregistered User'

            signing_user = user.User(signing_username)
            signing['signerName'] = f"{signing_user.first_name} {signing_user.last_name}"
            signed_at_unixtime = signing.pop('signedAt')
            signing['signatureDateTime'] = datetime.utcfromtimestamp(signed_at_unixtime).isoformat()
            entry_hash = signing.pop('entryHash')

            if entry_hash != "unconfirmed":
                signing['proofLink'] = f"https://{factom_explorer_domain}/entry?hash={entry_hash}"

        for version in versions:

            prind_version_info = self.get_version(version['versionNumber'])

            created_at_unixtime = version.pop('versionCreatedAt')
            version['uploadedDateTime'] = datetime.utcfromtimestamp(created_at_unixtime).isoformat()
            version['hash'] = version.pop('documentHash')
            entry_hash = version.pop('entryHash')

            if entry_hash != "unconfirmed":
                version['proofLink'] = f"https://{factom_explorer_domain}/entry?hash={entry_hash}"

            try:
                uploaded_by_username = prind_version_info['uploadedBy']
                s3_version_id  = prind_version_info['s3VersionId']
                
                try:
                    uploaded_by_user = user.User(uploaded_by_username)
                    uploaded_by_fullname = f"{uploaded_by_user.first_name} {uploaded_by_user.last_name}"
                except errors.UserNotFound:
                    uploaded_by_fullname = "A User"

                version['uploadedBy'] = uploaded_by_fullname
            
            except KeyError:
                version['uploadedBy'] = "A User"
            
            version['ver'] = version.pop('index')
            version.pop('versionNumber')

            this_version = int(version['ver'])

            if (this_version == 0 or this_version == latest_version):
                version['signatures'] = latest_version_signatures
            else:
                version['signatures'] = []

            version["s3VersionId"] = s3_version_id
            version["uploadName"] = prind_version_info.get('filename')

        logger.debug(log.function_end_output(locals()))  

        return versions

def get_user_uploaded_document_versions(username):

        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("sk").eq("documentVersion") 
                                 & Key("data").begins_with(f"uploader_{username}_")
        )

        items = response.get('Items',[])

        document_versions = []
        
        for item in items:
            # filter out v0
            if item['pk'].split('_')[1] == 'v0':
                continue

            item['documentDid'] = item.pop('pk').split('_')[2]
            item.pop('sk')
            item.pop('data')

            document_versions.append(item)

        return document_versions

if __name__ == "__main__":

    pass
    
    #get_project("TestProject")
    #create_project("Test Project", "This is a test project", "West Street, Farnham, Surrey")



