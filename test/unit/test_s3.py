from unittest import TestCase, mock
from unittest.mock import patch, MagicMock, Mock
import time
import sys
import boto3
import os
import json
import common
from moto import mock_dynamodb2, mock_s3, mock_sts
from boto3.dynamodb.conditions import Key, Attr
sys.path.append('../../')

print(sys.version_info)

from data import populate_project_fields

current_directory = os.path.dirname(os.path.realpath(__file__))

def mock_send_email(*args, **kwargs):
    return

@mock_dynamodb2
class TestUser(TestCase):

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

        import s3 as s3_module
        self.s3_module = s3_module

        self.table = common.create_table()

        self.project_id = 'UnitTestProject'
        self.authenticating_username = '4a9d66e8-f725-4c24-be3d-d3bdd417cb08'
        self.invitee_username = '4a9d66e8-f725-4c24-be3d-d3bdd417111'
        self.invitee_email = 'invitee@user.com'
        self.sp_did = os.environ['SP_DID']

        authenticating_username = self.authenticating_username
        project_id = self.project_id


        test_items = [
            {"pk": f"user_{authenticating_username}", "sk": "userDid", "data": "did:fnds:15aad5242a0b0d878b8ba0416d9f4f6792dafe6e969c1f57ab305a3bc8e4e1da"},
            {"displayName": "Unit Test Project", "data": f"active_{project_id}", "sk": "project", "siteAddress": {"projectAddressRegion": "Test", "projectAddressPostalCode": "AB13 3BB", "projectAddressTown": "Test", "projectAddressLine3": "Test", "projectAddressLine1": "Test", "projectAddressCountry": "Test", "projectAddressLine2": "Test"}, "description": "This is a non-descript description", "pk": f"project_{project_id}", "reference": None},
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

    @mock_sts
    def test_get_sts(self):

      
        event = {
            "requestPath": f"/project/{self.project_id}/page/feasibility/get-sts",
            "method": "GET", 
            "path": {
                "project_id": self.project_id,
                "page": "feasibility",
            },
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            }
        }
        
        response = self.s3_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 200)

    @mock_s3
    def test_get_file_url(self):
 
        field = {
            "pk": "project_UnitTestProject",
            "sk": "field_inception_1",
            "id": "1",
            "title": "Please upload your project brief",
            "description": "The project brief is required for the project to start.  Everyone will use this document.",
            "type": "file",
            "editable": True,
            "fieldDetails": {
                "filename": "test.pdf",
                "tags": []
            }
        }

        document = [
            {
                "pk": "document_UnitTestProject/inception/1",
                "sk": "document",
                "data": "did:fnds:12345678",
                "s3BucketName": "test_bucket",
                "s3Key": "UnitTestProject/inception/1"
            },
            {
                "pk": "document_v0_UnitTestProject/inception/1",
                "sk": "documentVersion",
                "data": "uploader_4a9d66e8-f725-4c24-be3d-d3bdd417cb08_2021-02-21T15:11:38.477867",
                "s3VersionId": "9b4be25c-c414-4696-a12a-be5356a6ded3",
                "versionNumber": 1,
                "filename": "test.pdf",
                "documentAttributes": [
                    {
                        "fieldName": "Filename",
                        "fieldValue": "test.pdf",
                        "fieldType": "Text"
                    },
                    {
                        "fieldName": "Project Name",
                        "fieldValue": "Unit Test Project",
                        "fieldType": "Text"
                    },
                    {
                        "fieldName": "Page Name",
                        "fieldValue": "inception",
                        "fieldType": "Text"
                    },
                    {
                        "fieldName": "Field Title",
                        "fieldValue": "Please upload your project brief",
                        "fieldType": "Text"
                    }
                ]
            },
            {
                "pk": "document_v1_UnitTestProject/inception/1",
                "sk": "documentVersion",
                "data": "uploader_4a9d66e8-f725-4c24-be3d-d3bdd417cb08_2021-02-21T15:11:38.477867",
                "s3VersionId": "9b4be25c-c414-4696-a12a-be5356a6ded3",
                "versionNumber": 1,
                "filename": "test.pdf",
                "documentAttributes": [
                    {
                        "fieldName": "Filename",
                        "fieldValue": "test.pdf",
                        "fieldType": "Text"
                    },
                    {
                        "fieldName": "Project Name",
                        "fieldValue": "Unit Test Project",
                        "fieldType": "Text"
                    },
                    {
                        "fieldName": "Page Name",
                        "fieldValue": "inception",
                        "fieldType": "Text"
                    },
                    {
                        "fieldName": "Field Title",
                        "fieldValue": "Please upload your project brief",
                        "fieldType": "Text"
                    }
                ]
            }
        ]

        items = [field, *document]

        print(items)
    
        for item in items:
            self.table.put_item(
                Item=  item
            )

        event = {
            "requestPath": f"/project/{self.project_id}/inception/1/1/get-file-url",
            "method": "GET", 
            "path": {
                "project_id": self.project_id,
                "page": "inception",
                "field_index": 1,
                "version": 1
            },
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            }
        }
        
        response = self.s3_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 200)

    @mock_sts
    def test_get_sts_profile_avatar(self):

      
        event = {
            "requestPath": "/user/get-sts/profile-avatar",
            "method": "GET", 
            "path": {},
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            }
        }
        
        response = self.s3_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 200)


