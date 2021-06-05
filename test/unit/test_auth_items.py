from unittest import TestCase, mock
from unittest.mock import patch, MagicMock, Mock
import time
import sys
import boto3
import os
import json
import common
from types import SimpleNamespace
from moto import mock_dynamodb2
from boto3.dynamodb.conditions import Key, Attr

sys.path.append("../../")

current_directory = os.path.dirname(os.path.realpath(__file__))


@mock_dynamodb2
class TestProcoreAuthItem(TestCase):
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

        from modules.auth import ProcoreAuthItem

        self.item_class = ProcoreAuthItem

        self.table = common.create_table()

    def tearDown(self):

        self.table.delete()

    def test_get(self):

        expected_item = self.item_class.item(
            cognito_username="1234",
            access_token="access-token",
            refresh_token="refresh-token",
            created_at=12512515,
            expires_at=12512523,
            lifetime=7200,
            authorised_projects=[2222]
        )

        self.table.put_item(Item=expected_item)

        returned_item = self.item_class.get(cognito_username="1234")

        self.assertDictEqual(returned_item, expected_item)

    def test_put(self):

        self.item_class.put(
            cognito_username="1234",
            access_token="access-token",
            refresh_token="refresh-token",
            created_at=12512515,
            expires_at=12512523,
            lifetime=7200,
            authorised_projects=[2222]
        )

        expected_item = {'pk': 'user#1234', 'sk': 'procoreAuthentication', 'accessToken': 'access-token', 'refreshToken': 'refresh-token', 'createdAt': '12512515', 'expiresAt': '12512523', 'lifetime': '7200', 'authorisedProjects': ['2222']}

        returned_item = self.item_class.get(
            cognito_username='1234'
        )

        self.assertDictEqual(returned_item, expected_item)
