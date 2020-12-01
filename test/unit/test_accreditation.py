from unittest import TestCase, mock
from mock import patch, MagicMock, Mock
import time
import sys
import boto3
import os
import json
import common
from moto import mock_dynamodb2, mock_lambda, mock_sqs
from boto3.dynamodb.conditions import Key, Attr
sys.path.append('../../')

print(sys.version_info)

# import accreditation

current_directory = os.path.dirname(os.path.realpath(__file__))

@mock_dynamodb2
class TestGetAccreditation(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.environment = mock.patch.dict(os.environ, {
                "TABLE_NAME": "prind-unittest",
                "AWS_REGION": "eu-west-1",
                "FOUNDATIONS_API_ID": "xxxxxx",
                "FOUNDATIONS_API_STAGE": "test",
                "SP_DID": "did:fnds:ca7722fabb7009aecf997a59973cd4fc810b820b15fd041b7671f146e97dcfc1",
                "FACTOM_EXPLORER_DOMAIN": "testnet.factoid.org"
            })
            
        cls.environment.start()

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        cls.environment.stop()

    def setUp(self):

        self.table = common.create_table()

    def tearDown(self):

        self.table.delete()

    def test_get_accreditation(self):

        import accreditation

        subject_did = 'did:fnds:31a24b270fe86d9c595e715854028c319cc75957718861eb66996929eb5c8025'
        project_id = 'UnitTestProject'
        subject_username = 'ab0ae262-eedf-41c0-ac6e-e5109217b6c1'
        requesting_username = '4a9d66e8-f725-4c24-be3d-d3bdd417cb08'

        test_items = [
            {"pk": f"user_{requesting_username}", "sk": "userDid", "data": "did:fnds:15aad5242a0b0d878b8ba0416d9f4f6792dafe6e969c1f57ab305a3bc8e4e1da"},
            {"pk": f"user_{subject_username}", "sk": "userDid", "data": f"did:{subject_did}"},
            {"displayName": "Unit Test Project", "data": project_id, "sk": "project", "siteAddress": {"projectAddressRegion": "Test", "projectAddressPostalCode": "AB13 3BB", "projectAddressTown": "Test", "projectAddressLine3": "Test", "projectAddressLine1": "Test", "projectAddressCountry": "Test", "projectAddressLine2": "Test"}, "description": "This is a non-descript description", "pk": f"project_{project_id}", "reference": None},
            {"pk": f"user_{requesting_username}", "sk": f"role_{project_id}", "data": "creator"},
            {"pk": f"user_{subject_username}", "sk": f"role_{project_id}", "data": "designer"},
            {"expiryTimestamp":1605217830, "apiKey_foundations": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJkaWQiOiJkaWQ6Zm5kczpjYTc3MjJmYWJiNzAwOWFlY2Y5OTdhNTk5NzNjZDRmYzgxMGI4MjBiMTVmZDA0MWI3NjcxZjE0NmU5N2RjZmMxIiwiZXhwIjoxNjA1MjE3ODMwfQ.KD_8hVXUkFhPOoac7Hk0BWlzRK4S5l3XvaOGOqFeYX77ZtTxB8xoj0ICzhKySk-iJ4p-qOlGU1JbD1QNobXACiCyZhrCL5aKc1y2vVE1hjZuR4oiUG7NgUcKsCkH9rTHIZfMb9FCRKeOjn1cjwPwCuFf6SQ0nescpnUQLPLGR4mMqHR30gVOrM9Cht1JVv0KVW08nAOstzJTKSpwbTWJhvsWVcuo8i6SgdyXDAbvtqJkrBuLaAESVNMpNk_GekqhCUoCbcfzL-7pu9bVkXjXZFw-amSKX943MpndZVF0ZCOMxS04M0cKL55eHtA1ICul2PojOP0E89dis2TLZzL21594EVPWZ5D5lOB1lvdRozrZLhJDYpmPxMfSEW_wbG8usCMUM0_Tv1SofjZZytP80h2W7bDrRQyPIlcvBEghjqdyMO-hTGZWXg-OOAutvFq09ObrpSydVJW3ZUKsl7sBCYzCuFg8SBpaok7MYBfeVEoX8-ole5u-EkY14nYDEyVcsNjoqKtEkRekdCm-YrudkvtOam1JYof_Xu9i98cJxOQ5CRS2a35e8QK1CFzu6tRjOvQIoRasYcvHD9m5NzMFhgxxuAre59Hi9Yumm9W6w_baYJmCLsK8Oqgmj9U_6pj0DK4En9wwHWd07A5SVlCqd6VB_v_9mko3mawgmvWQ4YM", "sk": "did:fnds:ca7722fabb7009aecf997a59973cd4fc810b820b15fd041b7671f146e97dcfc1", "pk": "apiKey_foundations"},
            {"pk": f"user_{subject_username}", "sk": "userDid", "data": subject_did},
            {"pk": f"user_{subject_username}", "sk": "userDetails_firstName", "data": "Ben"},
            {"pk": f"user_{subject_username}", "sk": "userDetails_lastName", "data": "Jeater"},
            {"pk": f"user_{requesting_username}", "sk": "userDetails_emailAddress", "data": "requester@user.com"},
            {"pk": f"user_{subject_username}", "sk": "accreditations", "accreditations": [{"accreditationName": "Construction Basics 1", "issuedDate": 1605213908, "issuer": "Acme Inc", "entryHash": "ee7514c2fe963160255645932f9f72416814b92a045b8dbba4ef6fb40b0c97d8"}]},
        ]

        for item in test_items:
            self.table.put_item(
                Item=  item
            )

        event = {
            "requestPath": f"/project/{project_id}/accreditation/{subject_did}",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub": requesting_username
            }, 
            "path": {
                "project_id": project_id,
                "foundations_id": subject_did
            }
        }

        response = accreditation.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['body'], [{'accreditationName': 'Construction Basics 1', 'issuedDate': 1605213908, 'issuer': 'Acme Inc', 'entryHash': 'ee7514c2fe963160255645932f9f72416814b92a045b8dbba4ef6fb40b0c97d8'}])
        self.assertEqual(response['statusCode'], 200)


