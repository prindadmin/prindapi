from unittest import TestCase, mock
from unittest.mock import patch, MagicMock, Mock
import time
import sys
import boto3
import os
import json
import common
from moto import mock_dynamodb2
from boto3.dynamodb.conditions import Key, Attr
sys.path.append('../../')

print(sys.version_info)

from data import populate_project_fields

current_directory = os.path.dirname(os.path.realpath(__file__))

def mock_send_email(*args, **kwargs):
    return

# @mock_s3
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

        import project as project_module
        self.project_module = project_module

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

        # load the default fields into the database
        populate_project_fields.load_fields(table=self.table)

    def tearDown(self):

        self.table.delete()

    def test_list_projects(self):
        
        event = {
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "requestPath": "/project/list",
            "method": "GET",
            "path": {}
        }

        response = self.project_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 200)

    def test_list_project_members(self):
        
        event = {
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "requestPath": f"/project/{self.project_id}/members",
            "method": "GET",
            "path": {
                "project_id": self.project_id
            }
        }

        response = self.project_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 200)

    def test_get_project(self):
        
        event = {
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "requestPath": f"/project/{self.project_id}",
            "method": "GET", 
            "path": {
                "project_id": self.project_id
            }
        }

        response = self.project_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 200)

    def test_create_project(self):
        
        event = { 
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "requestPath": "/project/create",
            "method": "POST",
            "body": {
               "projectName": "Test Project 10",
               "projectAddressLine1": "Test",
               "projectAddressLine2": "Test",
               "projectAddressLine3": "Test",
               "projectAddressTown": "Test",
               "projectAddressRegion": "Test",
               "projectAddressPostalCode": "AB12 3CD",
               "projectAddressCountry": "Test",
               "projectDescription": "This is a non-descript description",
               "projectReference": "123456",
               "projectType": "DHSFProject"
            }
        }

        response = self.project_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 201)

    def test_update_project(self):
        
        event = { 
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "requestPath": f"/project/{self.project_id}/update",
            "method": "POST",
            "path": {
                "project_id": self.project_id
            },
            "body": {
               "projectReference": "12345555"
            }
        }

        response = self.project_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 201)

    @mock.patch('modules.mail.send_email', side_effect=mock_send_email)
    def test_invite_user_to_project(self, mock_mail):
        
        event = {
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "requestPath": f"/project/{self.project_id}/invite-member",
            "method": "POST",
            "path": {
                "project_id": self.project_id
            },
            "body": {
                "emailAddress": self.invitee_email,
                "roleId": "projectConsultant"
            }
        }

        response = self.project_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 201)

        # print(common.database_snapshot(table=self.table))


    @mock.patch('modules.mail.send_email', side_effect=mock_send_email)
    def test_respond_to_project_invitation(self, mock_mail):
        
        
        invitation =     {
            "pk": "user_4a9d66e8-f725-4c24-be3d-d3bdd417111",
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
            "cognitoPoolClaims": {
                "sub": self.invitee_username
            },
            "requestPath": f"/project/{self.project_id}/respond-to-invitation",
            "method": "POST",
            "path": {
                "project_id":  self.project_id
            },
            "body": {
                "accepted": True
            }
        }

        response = self.project_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 201)

    @mock.patch('modules.mail.send_email', side_effect=mock_send_email)
    def test_remove_member_from_project(self, mock_mail):
        
        
        invitation_response_data =  [
            {
                "pk": "user_4a9d66e8-f725-4c24-be3d-d3bdd417111",
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
                "pk": "user_4a9d66e8-f725-4c24-be3d-d3bdd417111",
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
            "requestPath": f"/project/{self.project_id}/remove-member",
            "method": "POST",
            "path": {
                "project_id": self.project_id
            },
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "body": {
                "username": self.invitee_username
            }
        }

        response = self.project_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 201)

        # print(common.database_snapshot(table=self.table))

    def test_delete_project(self):
        
        event = {
            "requestPath": f"/project/{self.project_id}/delete",
            "method": "POST",
            "path": {
                "project_id": self.project_id
            },
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            }
        }

        response = self.project_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 200)



