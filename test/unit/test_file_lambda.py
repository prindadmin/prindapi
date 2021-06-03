from unittest import TestCase, mock
from unittest.mock import patch, Mock
import time
import sys
import os
import json
import boto3
import common
from moto import mock_dynamodb2, mock_ssm
from boto3.dynamodb.conditions import Key, Attr
from types import SimpleNamespace


sys.path.append("../../")
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

    if "rest/v1.0/folders" in args[0] and args[1]['project_id'] == 1234:

        status_code=403
        body={
            "message": "Invalid Project or Company"
        }

        return MockResponse(body, status_code)

    elif "/rest/v1.0/folders/" in args[0]:
        # calling the endpoint with folder_id
        status_code = 200
        with open(
            f"{current_directory}/fixtures/procore_files_response.json", "r"
        ) as response:
            body = json.loads(response.read())

        return MockResponse(body, status_code)

    elif args[0].endswith("/rest/v1.0/folders"):

        status_code = 200
        with open(
            f"{current_directory}/fixtures/procore_files_response.json", "r"
        ) as response:
            body = json.loads(response.read())

        return MockResponse(body, status_code)

    if "/rest/v1.0/file_versions" in args[0]:

        status_code = 200
        with open(
            f"{current_directory}/fixtures/procore_file_version_response.json", "r"
        ) as response:
            body = json.loads(response.read())

        return MockResponse(body, status_code)

    return MockResponse(None, 404)


def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.content = json.dumps(self.json_data).encode("utf-8")
            self.ok = self.status_code >= 200 and self.status_code <= 202

        def json(self):
            return self.json_data

    print(args[0])
    # update document on Foundations
    if args[0].endswith("/create"):

        body = {"statusCode": 202, "body": {"documentDid": "did:fnds:123456789"}}
        status_code = 202

    # create document on Foundations
    elif args[0].endswith("/update"):

        body = {"statusCode": 202, "body": {"documentVersionNumber": "2"}}
        status_code = 202

    # sign on Foundations
    elif 'signing-request' in args[0]:

        body = {"statusCode": 201, "body": {}}
        status_code = 201

    else:
        body = None
        status_code = 404

    return MockResponse(body, status_code)

@mock_ssm
@mock_dynamodb2
class TestFileLambda(TestCase):
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

        import file as module

        self.module = module

        from modules.auth import ProcoreAuth

        self.procore_auth_module = ProcoreAuth

        from modules.auth import ProcoreAuthItem

        self.table = common.create_table()

        common.add_secure_ssm_parameter(
            f"/foundations-procore-api/procore-client-secret/dev", "client-secret"
        )
        common.add_secure_ssm_parameter(
            "/foundations-procore-api/did_private_key/dev", "private-key"
        )

        self.authenticating_username = "4a9d66e8-f725-4c24-be3d-d3bdd417cb08"

        ProcoreAuthItem.put(
            cognito_username="4a9d66e8-f725-4c24-be3d-d3bdd417cb08",
            access_token="eyxxxxxxxxxxxxxxx",
            refresh_token="xxxxxxxxxxxxxxx",
            created_at=int(time.time()),
            expires_at=int(time.time()) + 7200,
            lifetime=7200,
            authorised_projects=['2222', '1234'],
        )
        self.foundations_api_key = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJkaWQiOiJkaWQ6Zm5kczpjYTc3MjJmYWJiNzAwOWFlY2Y5OTdhNTk5NzNjZDRmYzgxMGI4MjBiMTVmZDA0MWI3NjcxZjE0NmU5N2RjZmMxIiwiZXhwIjoxNjA1MjE3ODMwfQ.KD_8hVXUkFhPOoac7Hk0BWlzRK4S5l3XvaOGOqFeYX77ZtTxB8xoj0ICzhKySk-iJ4p-qOlGU1JbD1QNobXACiCyZhrCL5aKc1y2vVE1hjZuR4oiUG7NgUcKsCkH9rTHIZfMb9FCRKeOjn1cjwPwCuFf6SQ0nescpnUQLPLGR4mMqHR30gVOrM9Cht1JVv0KVW08nAOstzJTKSpwbTWJhvsWVcuo8i6SgdyXDAbvtqJkrBuLaAESVNMpNk_GekqhCUoCbcfzL-7pu9bVkXjXZFw-amSKX943MpndZVF0ZCOMxS04M0cKL55eHtA1ICul2PojOP0E89dis2TLZzL21594EVPWZ5D5lOB1lvdRozrZLhJDYpmPxMfSEW_wbG8usCMUM0_Tv1SofjZZytP80h2W7bDrRQyPIlcvBEghjqdyMO-hTGZWXg-OOAutvFq09ObrpSydVJW3ZUKsl7sBCYzCuFg8SBpaok7MYBfeVEoX8-ole5u-EkY14nYDEyVcsNjoqKtEkRekdCm-YrudkvtOam1JYof_Xu9i98cJxOQ5CRS2a35e8QK1CFzu6tRjOvQIoRasYcvHD9m5NzMFhgxxuAre59Hi9Yumm9W6w_baYJmCLsK8Oqgmj9U_6pj0DK4En9wwHWd07A5SVlCqd6VB_v_9mko3mawgmvWQ4YM"

        prerequisite_items = [
            {
                "expiryTimestamp": int(time.time() + 3600),
                "apiKey": self.foundations_api_key,
                "sk": os.environ["SP_DID"],
                "pk": "apiKey_foundations",
            },
        ]

        common.put_items(prerequisite_items, self.table)

    def tearDown(self):

        self.table.delete()
        common.delete_ssm_parameter(
            f"/foundations-procore-api/procore-client-secret/dev"
        )
        common.delete_ssm_parameter("/foundations-procore-api/did_private_key/dev")

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_list_files_at_root(self, mock_requests):

        event = {
            "cognitoPoolClaims": {"sub": self.authenticating_username},
            "method": "GET",
            "requestPath": "/procorefiles/company_id/project_id",
            "path": {"company_id": 1111, "project_id": 2222},
        }

        response = self.module.lambda_handler(event, {})

        self.assertEqual(response["statusCode"], 200)

        print(response)


    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_invalid_project(self, mocked_request):
        """
        Test that a 400 response is return with an error message saying
        "Invalid Project or Company" if the project ID doesn't exist on
        Procore
        """

        event = {
            "cognitoPoolClaims": {"sub": self.authenticating_username},
            "method": "GET",
            "requestPath": "/procorefiles/company_id/project_id",
            "path": {"company_id": 1111, "project_id": 1234},
        }

        response = self.module.lambda_handler(event, {})

        print(response)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['Error']['ErrorMessage'],  "Invalid Project or Company")

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_unauthorised_project(self, mocked_request):
        """
        Tests that an error response is returned if the project has not
        been specifically authorised by the user on Procore and stored in the ProcoreAuthItem
        in authorisedProjects
        """

        event = {
            "cognitoPoolClaims": {"sub": self.authenticating_username},
            "method": "GET",
            "requestPath": "/procorefiles/company_id/project_id",
            "path": {"company_id": 1111, "project_id": 4444},
        }

        response = self.module.lambda_handler(event, {})

        print(response)
        self.assertEqual(response['statusCode'], 400)
        self.assertEqual(response['Error']['ErrorMessage'],  "Your token is not valid for project 4444")

        response = self.table.scan()
        print(response['Items'])

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    def test_passes_folder_id_into_api_request(self, mock_requests):
        """
        Test that folder_id is passed into the URL on a /rest/v1/folders procore
        request if specified
        """

        event = {
            "cognitoPoolClaims": {"sub": self.authenticating_username},
            "method": "GET",
            "requestPath": "/procorefiles/company_id/project_id",
            "path": {"company_id": 1111, "project_id": 2222, "folder_id": 4444},
        }

        response = self.module.lambda_handler(event, {})

        self.assertEqual(response["statusCode"], 200)
        mock_requests.assert_called_with(
            "https://sandbox.procore.com/rest/v1.0/folders/4444",
            {'project_id': 2222},
            headers={'Procore-Company-Id': '1111', 'Authorization': 'Bearer eyxxxxxxxxxxxxxxx'},
        )

