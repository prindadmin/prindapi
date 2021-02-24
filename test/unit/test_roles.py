from unittest import TestCase, mock
from mock import patch, MagicMock, Mock
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

@mock_dynamodb2
class TestRole(TestCase):

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

        import roles as roles_module
        self.roles_module = roles_module

        self.authenticating_username = '4a9d66e8-f725-4c24-be3d-d3bdd417cb08'

        self.table = common.create_table()

        authenticating_username = self.authenticating_username


        test_items = [
            {"pk": f"user_{authenticating_username}", "sk": "userDid", "data": "did:fnds:15aad5242a0b0d878b8ba0416d9f4f6792dafe6e969c1f57ab305a3bc8e4e1da"},
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

    def tearDown(self):

        self.table.delete()

    def test_list_roles(self):
        
        event = {
            "cognitoPoolClaims": {
                "sub": self.authenticating_username
            },
            "requestPath": "/roles/get-roles",
            "method": "GET",
            "path": {}
        }

        response = self.roles_module.lambda_handler(event, {})

        print(response)

        self.assertEqual(response['statusCode'], 200)





