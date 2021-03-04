from unittest import TestCase, mock
from unittest.mock import patch, MagicMock, Mock
import time
import sys
import boto3
import os
import json
import common
from moto import mock_dynamodb2, mock_s3, mock_lambda, mock_sqs
from boto3.dynamodb.conditions import Key, Attr
sys.path.append('../../')

print(sys.version_info)

from data import populate_project_fields

current_directory = os.path.dirname(os.path.realpath(__file__))

def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.content =  json.dumps(self.json_data).encode('utf-8')

        def json(self):
            return self.json_data

    if args[0].endswith('/sp/document/create'):
        return MockResponse(
            {
                "statusCode": 202,
                "body": {
                    "documentDid": "did:fnds:12345678"
                }
            }, 
            202)

    return MockResponse(None, 404)

@mock_s3
@mock_dynamodb2
class TestPostField(TestCase):

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

        import field as field_module
        self.field_module = field_module

        self.table = common.create_table()

        self.project_id = 'UnitTestProject'
        self.authenticating_username = '4a9d66e8-f725-4c24-be3d-d3bdd417cb08'
        self.sp_did = os.environ['SP_DID']

        authenticating_username = self.authenticating_username
        project_id = self.project_id


        test_items = [
            {"pk": f"user_{authenticating_username}", "sk": "userDid", "data": "did:fnds:15aad5242a0b0d878b8ba0416d9f4f6792dafe6e969c1f57ab305a3bc8e4e1da"},
            {"displayName": "Unit Test Project", "data": project_id, "sk": "project", "siteAddress": {"projectAddressRegion": "Test", "projectAddressPostalCode": "AB13 3BB", "projectAddressTown": "Test", "projectAddressLine3": "Test", "projectAddressLine1": "Test", "projectAddressCountry": "Test", "projectAddressLine2": "Test"}, "description": "This is a non-descript description", "pk": f"project_{project_id}", "reference": None},
            {"pk": f"user_{authenticating_username}", "sk": f"role_{project_id}", "data": "creator"},
            {"expiryTimestamp":int(time.time() + 3600), "apiKey": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJkaWQiOiJkaWQ6Zm5kczpjYTc3MjJmYWJiNzAwOWFlY2Y5OTdhNTk5NzNjZDRmYzgxMGI4MjBiMTVmZDA0MWI3NjcxZjE0NmU5N2RjZmMxIiwiZXhwIjoxNjA1MjE3ODMwfQ.KD_8hVXUkFhPOoac7Hk0BWlzRK4S5l3XvaOGOqFeYX77ZtTxB8xoj0ICzhKySk-iJ4p-qOlGU1JbD1QNobXACiCyZhrCL5aKc1y2vVE1hjZuR4oiUG7NgUcKsCkH9rTHIZfMb9FCRKeOjn1cjwPwCuFf6SQ0nescpnUQLPLGR4mMqHR30gVOrM9Cht1JVv0KVW08nAOstzJTKSpwbTWJhvsWVcuo8i6SgdyXDAbvtqJkrBuLaAESVNMpNk_GekqhCUoCbcfzL-7pu9bVkXjXZFw-amSKX943MpndZVF0ZCOMxS04M0cKL55eHtA1ICul2PojOP0E89dis2TLZzL21594EVPWZ5D5lOB1lvdRozrZLhJDYpmPxMfSEW_wbG8usCMUM0_Tv1SofjZZytP80h2W7bDrRQyPIlcvBEghjqdyMO-hTGZWXg-OOAutvFq09ObrpSydVJW3ZUKsl7sBCYzCuFg8SBpaok7MYBfeVEoX8-ole5u-EkY14nYDEyVcsNjoqKtEkRekdCm-YrudkvtOam1JYof_Xu9i98cJxOQ5CRS2a35e8QK1CFzu6tRjOvQIoRasYcvHD9m5NzMFhgxxuAre59Hi9Yumm9W6w_baYJmCLsK8Oqgmj9U_6pj0DK4En9wwHWd07A5SVlCqd6VB_v_9mko3mawgmvWQ4YM", "sk": self.sp_did, "pk": "apiKey_foundations"},
            {"pk": f"user_{authenticating_username}", "sk": "userDetails_emailAddress", "data": "requester@user.com"},
        ]

        for item in test_items:
            self.table.put_item(
                Item=  item
            )

        # load the default fields into the database
        populate_project_fields.load_fields(table=self.table)

    def tearDown(self):

        self.table.delete()

    def test_post_dropdown(self):
        
        event = {
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "path": {
                "project_id": self.project_id,
                "page": "feasibility",
                "field_index": 2
            },
            "body": {
                "fieldDetails": {
                  "dropdownValue": "No",
                  "textboxValue": ".",
                  "dropdownOptions": [
                    {
                      "id": "1",
                      "name": "Yes"
                    },
                    {
                      "id": "2",
                      "name": "No"
                    }
                  ],
                  "optionOpensTextBox": "Yes"
                },
                "title": "This is a test drop-down box", 
                "description": "This is a test field",
                "type": "dropdown",
                "editable": True
            }
        }

        response = self.field_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 200)

    @mock.patch('requests.post', side_effect=mocked_requests_post)
    def test_post_file(self, mock_post):
        
        event = {
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "path": {
                "project_id": self.project_id,
                "page": "inception",
                "field_index": 1
            },
            "body": {
                "type": "file",
                "fieldDetails": {
                    "filename": "test.pdf",
                    "tags": []
                },
            }
        }

        bucket = common.create_bucket_with_versioning(os.environ['S3_BUCKET_NAME'])

        bucket.put_object(
            Key=f'{self.project_id}/inception/1', 
            Body=(bytes(json.dumps({'data': 'test'}).encode('UTF-8')))
        )

        response = self.field_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 200)

        s3_object = bucket.Object(f'{self.project_id}/inception/1')
        response = s3_object.get()


