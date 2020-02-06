import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors
from modules import project




# If logger hasn"t been set up by a calling function, set it here

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

class Page(project.Project):

    def __init__(self, page, project_id):

        project.Project.__init__(self, project_id=project_id)

        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"defaultField_{page}")
        )

        try:
            items = response['Items']
        except KeyError:
            raise errors.PageNotFound(f"A page with name {page} was not found.")


        self.page_name = page
        self.default_fields = items

    def get_populated_fields(self):

        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"project_{self.project_id}") & Key("sk").begins_with(f"field_{self.page_name}")
        )

        try:
            items = response['Items']
        except KeyError:
            items = []

        populated_fields = {}
        
        for item in items:
            item.pop('pk')
            item.pop('sk')
            
            populated_fields[str(item["id"])] = item

        return populated_fields

    def get_resultant_fields(self):

        populated_fields = self.get_populated_fields()
        resultant_fields = []

        for default in self.default_fields:
            try:
                value_for_this_index = populated_fields[default['id']]
                resultant_fields.append(value_for_this_index)
            except KeyError:
                resultant_fields.append(default)

        return resultant_fields

    def write_field(self, field_index, field_data, title, description, field_type, editable=True):

        """
        If a document, field_data is:

        "fieldDetails": {
          "documentDid": "did:fnds:a1cbe1b4c646e28f430273fe9536bcd15a7d36a04d9ffaf77b7962e63535a2fa"
        }

        Otherwise fieldDetails is exactly the same as what was downloaded
        """

        table.put_item(
            Item={
                "pk": f"project_{self.project_id}",
                "sk": f"field_{self.page_name}_{field_index}",
                "id": str(field_index),
                "title": title,
                "description": description,
                "type": field_type,
                "editable": editable,
                "fieldDetails": field_data
                
            }
        )










