from unittest import TestCase, mock
from unittest.mock import patch, MagicMock, Mock
import time
import sys
import boto3
import os
import json
import common
from types import SimpleNamespace
from moto import mock_dynamodb2, mock_ssm
from boto3.dynamodb.conditions import Key, Attr

sys.path.append("../../")
from modules import errors

current_directory = os.path.dirname(os.path.realpath(__file__))


def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.content = json.dumps(self.json_data).encode("utf-8")
            self.ok = self.status_code >= 200 and self.status_code <= 202

        def json(self):
            return self.json_data

    if args[0].endswith("/rest/v1.0/folders"):

        status_code = 200
        with open(f"{current_directory}/fixtures/procore_files_response.json", "r") as response:
            body = json.loads(response.read())

        return MockResponse(body, status_code)

    return MockResponse(None, 404)

@mock_ssm
@mock_dynamodb2
class TestProject(TestCase):
    @classmethod
    def setUpClass(cls):

        cls.environment = mock.patch.dict(os.environ, common.environment)
        cls.environment.start()

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        cls.environment.stop()

    def setUp(self):

        from modules.procore_project import Project

        self.test_class = Project

        self.table = common.create_table()

        common.add_secure_ssm_parameter(
            f'/foundations-procore-api/procore-client-secret/dev', 
            'client-secret')
    
        from modules.auth import ProcoreAuthItem
           
        ProcoreAuthItem.put(
            cognito_username='4a9d66e8-f725-4c24-be3d-d3bdd417cb08',
            access_token='eyxxxxxxxxxxxxxxx',
            refresh_token='xxxxxxxxxxxxxxx',
            created_at=int(time.time()),
            expires_at=int(time.time())+7200,
            lifetime=7200,
            authorised_projects=['2222']
        )

    def tearDown(self):

        self.table.delete()
        common.delete_ssm_parameter(f'/foundations-procore-api/procore-client-secret/dev')

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_get_procore_files(self, mock_get):

        test_project = self.test_class("1111", "2222")
        procore_files = test_project.get_procore_files(cognito_username='4a9d66e8-f725-4c24-be3d-d3bdd417cb08')

        print(procore_files)




