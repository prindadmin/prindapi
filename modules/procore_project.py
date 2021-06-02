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
            'Procore-Company-Id': str(self.company_id),
            'Authorization': f'Bearer {access_token}'
        }

        url = f'{base_url}/rest/v1.0/folders'

        if folder_id is not None:
            url = f'{url}/{folder_id}'


        response = requests.get(url, params, headers=headers)

        data = response.json()

        if not response.ok:
            logger.error('Procore returned a status code of {}'.format(response.status_code))
            logger.error(data)
            raise errors.ProcoreApiError(data.get('message'))

        return data

                