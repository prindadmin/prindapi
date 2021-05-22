from unittest import TestCase, mock
from unittest.mock import patch, MagicMock, Mock
import time
import sys
import boto3
import os
import json
import common
from freezegun import freeze_time
from types import SimpleNamespace
from moto import mock_dynamodb2, mock_ssm
from boto3.dynamodb.conditions import Key, Attr

sys.path.append("../../")
from modules import errors

current_directory = os.path.dirname(os.path.realpath(__file__))

@freeze_time('2020-01-01')
def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.content = json.dumps(self.json_data).encode("utf-8")
            self.ok = self.status_code >= 200 and self.status_code <= 202

        def json(self):
            return self.json_data

    if args[0].endswith("/oauth/token"):

        params = args[1]
        print(params)
        if params.get('code'):
            if params["code"] == "valid-auth-code":
                status_code = 200
                body = {
                    "access_token": "eyxxxxxxxxxxxxxxx",
                    "token_type": "Bearer",
                    "expires_in": 7200,
                    "refresh_token": "xxxxxxxxxxxxxxx",
                    "created_at": int(time.time())
                }
            else:
                status_code = 401
                body = {}
        elif params.get('refresh_token'):
            status_code = 200
            body = {
                "access_token": "eyxxxxxxxxxxxxxxx",
                "token_type": "Bearer",
                "expires_in": 7200,
                "refresh_token": "xxxxxxxxxxxxxxx",
                "created_at": int(time.time())
            }
        else:
            status_code = 401
            body = {}

        return MockResponse(body, status_code)

    return MockResponse(None, 404)


@mock_ssm
@mock_dynamodb2
@freeze_time('2020-01-01')
class TestProcoreAuth(TestCase):
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

        from modules.auth import ProcoreAuth

        self.item_class = ProcoreAuth

        self.table = common.create_table()

        common.add_secure_ssm_parameter(
            f'/prind-api/procore-client-secret/dev', 
            'client-secret')

    def tearDown(self):

        self.table.delete()
        common.delete_ssm_parameter(f'/prind-api/procore-client-secret/dev')

    @mock.patch("requests.post", side_effect=mocked_requests_post)
    def test_request_access_token_success(self, mock_requests):

        response = self.item_class.request_access_token_with_auth_code(
            "valid-auth-code", "http://redirect_uri=localhost:3000/procore-auth"
        )

        expected_response = {
            "access_token": "eyxxxxxxxxxxxxxxx",
            "token_type": "Bearer",
            "expires_in": 7200,
            "refresh_token": "xxxxxxxxxxxxxxx",
            "created_at": int(time.time())
        }

        self.assertDictEqual(response, expected_response)

    @mock.patch("requests.post", side_effect=mocked_requests_post)
    def test_request_access_token_failure(self, mock_requests):

        
        self.assertRaises(
            errors.InvalidProcoreAuth,
            self.item_class.request_access_token_with_auth_code,
            "invalid-auth-code", 
            "http://redirect_uri=localhost:3000/procore-auth"
        )

    @mock.patch("requests.post", side_effect=mocked_requests_post)
    def test_valid_auth_token(self, mock_requests):

        from modules.auth import ProcoreAuthItem
        ProcoreAuthItem.put(
            cognito_username='1111-2222-3333',
            access_token='aaaaa',
            refresh_token='bbbbb',
            created_at=1515151515,
            expires_at=1515151516,
            lifetime=1
        )
        response = self.item_class.valid_access_token(cognito_username='1111-2222-3333')

        auth_item = ProcoreAuthItem.get(cognito_username='1111-2222-3333')

        self.assertEqual(int(auth_item['expiresAt']), int(time.time()) + 7200)
            
