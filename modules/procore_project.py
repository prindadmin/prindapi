import boto3
import time
import json
import os
import requests
from datetime import datetime

from modules import log
from modules import errors

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules.auth import ProcoreAuth

# If logger hasn"t been set up by a calling function, set it here
try:
    logger
except:
    from modules.log import logger
    log.set_logging_level()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


class Project():
    def __init__(self, company_id, project_id):
        self.company_id = company_id
        self.project_id = project_id

    def get_procore_files(self, cognito_username, folder_id=None):

        print('folder_id in get_procore_files is', folder_id)

        if not ProcoreAuth.valid_access_token(cognito_username):
            raise errors.InvalidProcoreAuth('Your token can no longer be refreshed')

        base_url = os.environ['PROCORE_BASE_URL']
        auth_item = ProcoreAuth.retrieve_auth_token(cognito_username)
        access_token = auth_item['accessToken']
        
        params = dict(project_id=self.project_id)

        headers={
            'Authorization': f'Bearer {access_token}'
        }

        url = f'{base_url}/rest/v1.0/folders'

        if folder_id is not None:
            url = f'{url}/{folder_id}'


        response = requests.get(url, params, headers=headers)

        data = response.json()

        if not response.ok:
            raise errors.ProcoreApiError(data['message'])

        return data

    # def merge_anchors_and_signatures(self, cognito_username, folder_id=None):

    #     print('folder_id in merge_anchors_and_signatures is', folder_id)

    #     procore_data = self.get_procore_files(cognito_username, folder_id)
    #     signatures = self.get_signed_document_versions()
    #     anchors = self.get_anchored_document_versions()

    #     for file in procore_data.get('files', []):
    #         for version in file['file_versions']:
    #             version_signatures = signatures.get(f'{self.company_id}#{self.project_id}#{version["file_id"]}#{version["id"]}')
    #             if version_signatures:
    #                 print(version_signatures)
    #                 version['signatures'] = [
    #                     dict(
    #                         signed_by_user_id=version_signature.cognito_username,
    #                         signed_at=version_signature.signed_at,
    #                         signature=version_signature.signature,
    #                         signing_did=version_signature.signing_did,
    #                         signing_did_version=version_signature.signing_did_version,
    #                         signing_key=version_signature.signing_key,
    #                         signed_string=version_signature.signed_string,
    #                         signed_by=version_signature.signed_by,
    #                         entry_hash=version_signature.entry_hash
    #                     )
    #                     for version_signature
    #                     in version_signatures
    #                 ]
    #             else:
    #                 version['signatures'] = list()
    #             version_anchor = anchors.get(f'{self.company_id}#{self.project_id}#{version["file_id"]}#{version["id"]}')
    #             if version_anchor:
    #                 version['anchor'] = dict(
    #                     did=version_anchor.did,
    #                     foundations_version=version_anchor.foundations_version,
    #                     entry_hash=version_anchor.entry_hash,
    #                     created_at=version_anchor.created_at,
    #                 )
    #             else:
    #                 version['anchor'] = dict()

    #     return procore_data

                