from unittest import TestCase, mock
from unittest.mock import patch, MagicMock, Mock
import time
import sys
import boto3
import os
import json
import common
from freezegun import freeze_time
from moto import mock_dynamodb2, mock_ssm
from boto3.dynamodb.conditions import Key, Attr
sys.path.append('../../')

from data import populate_project_fields

current_directory = os.path.dirname(os.path.realpath(__file__))

def mock_send_email(*args, **kwargs):
    return

def mocked_requests_post(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code
            self.content = json.dumps(self.json_data).encode("utf-8")

        def json(self):
            return self.json_data

        def ok(self):
            if self.status_code >= 200 and self.status_code <= 202:
                return True
            return False

    if args[0].endswith("/oauth/token"):

        params = args[1]
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

def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.status_code = status_code
            self.content = json_data
            self.ok = self.status_code >= 200 and self.status_code <= 202
            self.url = args[0]
            self.json_data = json_data

        def json(self):
            return self.json_data

    if "/rest/v1.0/me" in args[0]:

        if args[1]['project_id'] == 2222:

            status_code = 200
            body = {
                "id": 160586,
                "login": "exampleuser@website.com",
                "name": "Carl Contractor"
            }

        else:
            status_code = 403
            body = {}

        return MockResponse(body, status_code)

    return MockResponse(None, 404)

@freeze_time('2020-01-01')
@mock_ssm
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

        import user as user_module
        self.user_module = user_module

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

            {"pk": f"user_{self.invitee_username}", "sk": "userDetails_emailAddress", "data": self.invitee_email},

            {'pk': 'role_contractor', 'sk': 'role-name', 'data': 'Contractor'},
            {'pk': 'role_creator', 'sk': 'role-name', 'data': 'Creator'},
            {'pk': 'role_designer', 'sk': 'role-name', 'data': 'Designer'},
            {'pk': 'role_principalContractor', 'sk': 'role-name', 'data': 'Principal Contractor'},
            {'pk': 'role_principalDesigner', 'sk': 'role-name', 'data': 'Principal Designer'},
            {'pk': 'role_projectConsultant', 'sk': 'role-name', 'data': 'Project Consultant'}
        ]

        for item in test_items:
            self.table.put_item(
                Item=  item
            )

        import user as module
        self.module = module

        from modules.auth import ProcoreAuth
        self.procore_auth_module = ProcoreAuth

        common.add_secure_ssm_parameter(
            f'/prind-api/procore-client-secret/dev', 
            'client-secret')

        self.authenticating_username = '4a9d66e8-f725-4c24-be3d-d3bdd417cb08'

    def tearDown(self):

        self.table.delete()
        common.delete_ssm_parameter(f'/prind-api/procore-client-secret/dev')

    def test_get_project_invitations(self):

        invitee_username = "4a9d66e8-f725-4c24-be3d-d3bdd417111"

        invitation =     {
            "pk": f'user_{invitee_username}',
            "sk": "roleInvitation_UnitTestProject",
            "data": "projectConsultant",
            "requestedBy": "4a9d66e8-f725-4c24-be3d-d3bdd417cb08",
            "requestedAt": "1613904516",
            "roleName": "Project Consultant",
            "inviteeFirstName": None,
            "inviteeLastName": None,
            "inviteeEmailAddress": "invitee@user.com"
        }

        self.table.put_item(
            Item=  invitation
        )
        
        event = {
            "requestPath": "/user/get-project-invitations",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub": invitee_username
            }
        }

        response = self.user_module.lambda_handler(event, {})

        self.assertEqual(response['statusCode'], 200)

    def test_get_accessible_projects(self):

        authenticating_username = "4a9d66e8-f725-4c24-be3d-d3bdd417111"

        invitation_response_data =  [
            {
                "pk": f"user_{authenticating_username}",
                "sk": "roleInvitationResponse_UnitTestProject",
                "data": "projectConsultant",
                "requestedBy": "4a9d66e8-f725-4c24-be3d-d3bdd417cb08",
                "requestedAt": "1613904516",
                "roleName": "Project Consultant",
                "inviteeFirstName": None,
                "inviteeLastName": None,
                "inviteeEmailAddress": "invitee@user.com",
                "accepted": True,
                "respondedAt": "1613905639"
            },
            {
                "pk":  f"user_{authenticating_username}",
                "sk": "role_UnitTestProject",
                "data": "projectConsultant",
                "dateJoined": "1613905639"
            }
        ]

        for item in invitation_response_data:
            self.table.put_item(
                Item=  item
            )

      
        event = {
            "requestPath": "/user/get-accessible-projects",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub": authenticating_username
            }
        }

        response = self.user_module.lambda_handler(event, {})

        self.assertEqual(response['statusCode'], 200)

    def test_get_profile(self):

        authenticating_username = "4a9d66e8-f725-4c24-be3d-d3bdd417111"

        event = {
            "requestPath": "/user/profile",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub":authenticating_username
            }
        }

        response = self.user_module.lambda_handler(event, {})

        self.assertEqual(response['statusCode'], 200)


    def test_get_history(self):

        authenticating_username = "4a9d66e8-f725-4c24-be3d-d3bdd417111"

        event = {
            "requestPath": "/user/get-history",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub": authenticating_username
            }
        }

        response = self.user_module.lambda_handler(event, {})

        self.assertEqual(response['statusCode'], 200)


    def test_get_signature_requests(self):

        authenticating_username = "4a9d66e8-f725-4c24-be3d-d3bdd417111"

        signature_request = {    
            "pk": f"user_{authenticating_username}",
            "sk": f"documentSignRequest_{self.project_id}/inception/1",
            "requestedBy": self.authenticating_username,
            "requesterFirstName": "Bob",
            "requesterLastName": "Jones",
            "requestedAt": str(int(time.time())),
            "fieldTitle": "Test Document To Sign"
        }

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

        items = [signature_request, field, *document]
    
        for item in items:
            self.table.put_item(
                Item=  item
            )

        event = {
            "requestPath": "/user/get-signature-requests",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub": authenticating_username
            }
        }
        
        response = self.user_module.lambda_handler(event, {})

        self.assertEqual(response['statusCode'], 200)

    @mock.patch("requests.post", side_effect=mocked_requests_post)
    def test_request_access_token_with_auth_code(self, mock_requests):


        event = {
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "method": "POST",
            "requestPath": "/user/authoriseprocore",
            "path": {},
            "body": {
                "code": "valid-auth-code",
                "redirectURI": "http://localhost:3000/procore-auth",
                "companyId": '1111',
                "projectId": '2222'
            }
        }

        response = self.module.lambda_handler(event, {})

        stored_item = self.procore_auth_module.retrieve_auth_token(self.authenticating_username)
        expected_item = {'pk': f'user#{self.authenticating_username}', 'sk': 'procoreAuthentication', 'accessToken': 'eyxxxxxxxxxxxxxxx', 'refreshToken': 'xxxxxxxxxxxxxxx', 'createdAt': '1577836800', 'expiresAt': '1577844000', 'lifetime': '7200'}

        self.assertDictEqual(stored_item, expected_item)

        mock_requests.assert_called_with(
            'https://login-sandbox.procore.com/oauth/token',
            {
                'grant_type': 'authorization_code',
                'client_id': '238a7b66f9d4494a4e70612973c30af168d44e2c5291a6a71bb4306dcc5787fc',
                'client_secret': 'client-secret',
                'redirect_uri': 'http://localhost:3000/procore-auth',
                'code': 'valid-auth-code'
                }
            )

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    @mock.patch("requests.post", side_effect=mocked_requests_post)
    def test_checkprocoreaccess_with_refresh_token_and_authorised_project(self, mock_requests_post, mock_requests_get):
        """
        The user has previously authorised on Procore with
        this project and has a refresh token stored in the
        database
        """
        from modules.auth import ProcoreAuthItem
        ProcoreAuthItem.put(
            cognito_username='4a9d66e8-f725-4c24-be3d-d3bdd417cb08',
            access_token='aaaaa',
            refresh_token='bbbbb',
            created_at=1515151515,
            expires_at=1515151516,
            lifetime=1
        )

        event = {
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "method": "GET",
            "requestPath": "/user/checkprocoreaccess/{company_id}/{project_id}",
            "path": {
                "company_id": "1111",
                "project_id": "2222"
            },
            "body": {}
        }
        response = self.module.lambda_handler(event, {})

        self.assertEqual(response['statusCode'], 200)
        
        mock_requests_post.assert_called_with(
            'https://login-sandbox.procore.com/oauth/token',
            {
                'grant_type': 'refresh_token',
                'client_id': '238a7b66f9d4494a4e70612973c30af168d44e2c5291a6a71bb4306dcc5787fc',
                'client_secret': 'client-secret',
                'redirect_uri': None,
                'refresh_token':
                'bbbbb'
            }
        )

        mock_requests_get.assert_called_with(
            'https://sandbox.procore.com/rest/v1.0/me',
            {
                'project_id': 2222
            },
            headers={
                'Procore-Company-Id': '1111',
                'Authorization': 'Bearer eyxxxxxxxxxxxxxxx'
            }
        )

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    @mock.patch("requests.post", side_effect=mocked_requests_post)
    def test_checkprocoreaccess_with_refresh_token_and_unauthorised_project(self, mock_requests_post, mock_requests_get):
        """
        The user has previously authorised with Procore and has a refresh
        token in the database, but the response from Procure says that
        they are not authorised with this project
        """

        from modules.auth import ProcoreAuthItem
        ProcoreAuthItem.put(
            cognito_username='4a9d66e8-f725-4c24-be3d-d3bdd417cb08',
            access_token='aaaaa',
            refresh_token='bbbbb',
            created_at=1515151515,
            expires_at=1515151516,
            lifetime=1
        )

        event = {
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "method": "GET",
            "requestPath": "/user/checkprocoreaccess/{company_id}/{project_id}",
            "path": {
                "company_id": "1111",
                "project_id": "8888"
            },
            "body": {}
        }
        response = self.module.lambda_handler(event, {})

        self.assertEqual(response['statusCode'], 400)

        mock_requests_post.called_with(
            'https://login-sandbox.procore.com/oauth/token',
            {
                'grant_type': 'refresh_token',
                'client_id': '238a7b66f9d4494a4e70612973c30af168d44e2c5291a6a71bb4306dcc5787fc',
                'client_secret': 'client-secret',
                'redirect_uri': None,
                'refresh_token': 'bbbbb'
            }
        )

        mock_requests_get.assert_called_with(
            'https://sandbox.procore.com/rest/v1.0/me',
            {
                'project_id': 8888
            },
            headers={
                'Procore-Company-Id': '1111',
                'Authorization': 'Bearer eyxxxxxxxxxxxxxxx'
            }
        )

    @mock.patch("requests.get", side_effect=mocked_requests_get)
    @mock.patch("requests.post", side_effect=mocked_requests_post)
    def test_checkprocoreaccess_without_refresh_token(self, mock_requests_post, mock_requests_get):
        """
        The user has not previous authorised on any project and does not have a
        refresh token stored in the database
        """

        event = {
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "method": "GET",
            "requestPath": "/user/checkprocoreaccess/{company_id}/{project_id}",
            "path": {
                "company_id": "1111",
                "project_id": "2222"
            },
            "body": {}
        }
        response = self.module.lambda_handler(event, {})

        self.assertEqual(response['statusCode'], 400)

        mock_requests_post.assert_not_called()

        mock_requests_get.assert_not_called()
