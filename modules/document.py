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
from modules import project
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
factom_explorer_domain = os.environ["FACTOM_EXPLORER_DOMAIN"]

# foundations_jwt = auth.get_foundations_jwt(sp_did)

class Document():

    def __init__(self, project_id, page, field_index):

        # logger.info(log.function_start_output())

        response = table.get_item(
            Key={
                "pk": f"document_{project_id}/{page}/{field_index}",
                "sk": "document"
            }
        )

        try:
            item = response['Item']
        except KeyError:
            raise errors.DocumentNotFound(f"A document was not found for field {project_id}/{page}/{field_index}.")

        self.project_id = project_id
        self.page = page
        self.field_index = field_index
        self.document_did = item['data']
        self.s3_bucket_name = item['s3BucketName']
        self.s3_key = item['s3Key']
        self.filename = None

        logger.debug(log.function_end_output(locals()))  

    def get_version(self, version):

        response = table.get_item(
            Key={
                "pk": f"document_v{version}_{self.project_id}/{self.page}/{self.field_index}",
                "sk": "documentVersion"
            }
        )

        try:
            item = response['Item']
        except KeyError:
            raise errors.DocumentVersionNotFound(f"Version {version} of document {self.project_id}/{self.page}/{self.field_index} does not exist")

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

        version = get_version(0)  

        return int(version['versionNumber'])

    def get_foundations_info(self):

        foundations_jwt = auth.get_foundations_jwt(sp_did)

        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{self.document_did}/versions"

        logger.info(f"api_url is {api_url}")

        params = {}

        response = requests.get(
            api_url,
            params=params,
            headers={'Authorization': foundations_jwt}
        )

        response_dict = json.loads(response.content.decode('utf-8'))

        if response_dict.get("statusCode") != 200:
            logger.error(f"error calling /sp/document-did/{self.document_did}/versions: {response_dict}")
            raise errors.FoundationsApiError(f"error calling /sp/document-did/{self.document_did}/versions")
        else:
            logger.info(f"response from /sp/document-did/{self.document_did}/versions is {response_dict}")
            versions = response_dict['body']

        logger.debug(log.function_end_output(locals()))  

        return versions

    def get_version_signatures(self, version):

        foundations_jwt = auth.get_foundations_jwt(sp_did)

        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{self.document_did}/version-signatures/{version}"

        logger.info(f"api_url is {api_url}")

        params = {}

        response = requests.get(
            api_url,
            params=params,
            headers={'Authorization': foundations_jwt}
        )
        response_dict = json.loads(response.content.decode('utf-8'))    

        if response_dict.get("statusCode") != 200:
            logger.error(f"error calling /sp/document-did/{self.document_did}/version-signatures/{version}: {response_dict}")
            raise errors.FoundationsApiError(f"error calling /sp/document-did/{self.document_did}/version-signatures/{version}")
        else:
            logger.info(f"response from /sp/document-did/{self.document_did}/version-signatures/{version} is {response_dict}")
            signatures = response_dict['body']

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

            version["s3VersionId"] = prind_version_info['s3VersionId']
            version["uploadName"] = prind_version_info.get('filename')

        logger.debug(log.function_end_output(locals()))  

        return versions

    def update(self, file_hash, uploading_username, s3_version_id, filename):

        previous_version = self.get_version(0)
        
        if previous_version['s3VersionId'] == s3_version_id:
            raise errors.DocumentVersionExists('This version of the document already exists')
        
        foundations_jwt = auth.get_foundations_jwt(sp_did)

        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{self.document_did}/update"

        logger.info(f"api_url is: {api_url}")

        document_field = field.Field(
            field_index=self.field_index,
            page_name=self.page, 
            project_id=self.project_id 
        )

        document_attributes = [
            {
                "fieldName": "Filename",
                "fieldValue": filename,
                "fieldType": "Text"
            },
            {
                "fieldName": "Project Name",
                "fieldValue": project.Project(self.project_id).project_name,
                "fieldType": "Text"
            },
            {
                "fieldName": "Page Name",
                "fieldValue": self.page,
                "fieldType": "Text"
            },
            {
                "fieldName": "Field Title",
                "fieldValue": document_field.get()['title'],
                "fieldType": "Text"
            }
        ]

        params = {
            "documentHash": file_hash,
            "requesterReference": "File Uploader",
            "documentAttributes": document_attributes

        }
        
        logger.info(f"params are: {params}")

        response = requests.post(
            api_url,
            data=json.dumps(params),
            headers={'Authorization': foundations_jwt}
        )

        response_dict = json.loads(response.content.decode('utf-8'))

        if response_dict.get("statusCode") != 202:
            logger.error(f"error calling /sp/document-did/{self.document_did}/update: {response_dict}")
            raise errors.FoundationsApiError(f"error calling /sp/document-did/{self.document_did}/update")
        else:
            logger.info(f"response from /sp/document-did/{self.document_did}/update is {response_dict}")

        document_version_number = response_dict['body']['documentVersionNumber']
        datetime_suffix = datetime.utcnow().isoformat()
        
        # Prin-D database entries
        table.put_item(
            Item={    
                "pk": f"document_v0_{self.project_id}/{self.page}/{self.field_index}",
                "sk": "documentVersion",
                "data": f"uploader_{uploading_username}_{datetime_suffix}",
                "s3VersionId": s3_version_id,
                "versionNumber": document_version_number,
                "filename": filename,
                "documentAttributes": document_attributes
            }
        )

        table.put_item(
            Item={    
                "pk": f"document_v{document_version_number}_{self.project_id}/{self.page}/{self.field_index}",
                "sk": "documentVersion",
                "data": f"uploader_{uploading_username}_{datetime_suffix}",
                "s3VersionId": s3_version_id,
                "versionNumber": document_version_number,
                "filename": filename,
                "documentAttributes": document_attributes
            }
        )

def create(
    project_id,
    page,
    field_index,
    file_hash,
    uploading_username,
    s3_version_id,
    s3_bucket_name,
    s3_key,
    filename,
    document_name,
    document_tags=[]
):

    foundations_jwt = auth.get_foundations_jwt(sp_did)

    # Foundations API call
    api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document/create"

    logger.info(f"api_url is: {api_url}")

    document_field = field.Field(
        field_index=field_index,
        page_name=page, 
        project_id=project_id 
    )

    document_attributes = [
        {
            "fieldName": "Filename",
            "fieldValue": filename,
            "fieldType": "Text"
        },
        {
            "fieldName": "Project Name",
            "fieldValue": project.Project(project_id).project_name,
            "fieldType": "Text"
        },
        {
            "fieldName": "Page Name",
            "fieldValue": page,
            "fieldType": "Text"
        },
        {
            "fieldName": "Field Title",
            "fieldValue": document_field.get()['title'],
            "fieldType": "Text"
        }
    ]

    params = {
        "documentName": document_name,
        "documentHash": file_hash,
        "requesterReference": "File Uploader",
        "documentAttributes": document_attributes
    }

    logger.info(f"params are: {params}")

    response = requests.post(
        api_url,
        data=json.dumps(params),
        headers={'Authorization': foundations_jwt}
    )

    response_dict = json.loads(response.content.decode('utf-8'))

    if response_dict.get("statusCode") != 202:
        logger.error(f"error calling /sp/document/create: {response_dict}")
        raise errors.FoundationsApiError(f"error calling /sp/document/create")
    else:
        logger.info(f"response from /sp/document/create is {response_dict}")
      
    document_did = response_dict['body']['documentDid']

    datetime_suffix = datetime.utcnow().isoformat()

    table.put_item(
        Item={    
            "pk": f"document_{project_id}/{page}/{field_index}",
            "sk": "document",
            "data": document_did,  
            "s3BucketName": s3_bucket_name ,
            "s3Key": s3_key
        }
    )

    table.put_item(
        Item={    
            "pk": f"document_v0_{project_id}/{page}/{field_index}",
            "sk": "documentVersion",
            "data": f"uploader_{uploading_username}_{datetime_suffix}",
            "s3VersionId": s3_version_id,
            "versionNumber": 1,
            "filename": filename,
            "documentAttributes": document_attributes
        }
    )

    table.put_item(
        Item={    
            "pk": f"document_v1_{project_id}/{page}/{field_index}",
            "sk": "documentVersion",
            "data": f"uploader_{uploading_username}_{datetime_suffix}",
            "s3VersionId": s3_version_id,
            "versionNumber": 1,
            "filename": filename,
            "documentAttributes": document_attributes
        }
    )

    for tag in document_tags:
        table.put_item(
            Item={    
                "pk": f"document_{project_id}/{page}/{field_index}",
                "sk": f"documentTag_{tag}",
                "data": document_did 
            }
        )

    return document_did
    
def get_user_uploaded_document_versions(username):

        project_object = {}

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

            try:    
                item['projectId'] = item['pk'].split('_')[2].split('/')[0]
                item['page'] = item['pk'].split('_')[2].split('/')[1]
                item['field'] = item['pk'].split('_')[2].split('/')[2]
            except IndexError:
                # document might be stored in the old format, so skip it
                continue
            project_id = item['projectId']

            if not project_object.get(project_id):
                project_object[project_id] = project.Project(project_id)

            if not project_object[project_id].active:
                continue

            try:
                item['dateTime'] = item.pop('data').split('_')[2]
            except (KeyError, IndexError):
                item['dateTime'] = None


            item["projectName"] = project_object[project_id].project_name

            item.pop('pk')
            item.pop('sk')

            document_versions.append(item)

        return document_versions


def get_document_field(document_did):

    response = table.query(
        IndexName='GSI1',
        KeyConditionExpression=Key('sk').eq("document") & Key('data').eq(document_did)
    )

    try:
        item = response['Items'][0]
    except IndexError:
        raise errors.DocumentNotFound(f"A document was not found with the DID {document_did}")

    field_details = dict()

    field_details['projectId'] = item['pk'].split('_')[1].split('/')[0]
    field_details['page'] = item['pk'].split('_')[1].split('/')[1]
    field_details['field'] = item['pk'].split('_')[1].split('/')[2]

    return field_details


if __name__ == "__main__":

    pass
    
    #get_project("TestProject")
    #create_project("Test Project", "This is a test project", "West Street, Farnham, Surrey")



