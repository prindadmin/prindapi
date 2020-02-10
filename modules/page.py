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

    def write_field(self, field_index, field_type, field_data=None, title=None, description=None, editable=None):

        """
        If a document, field_data is:

        "fieldDetails": {
          "documentDid": "did:fnds:a1cbe1b4c646e28f430273fe9536bcd15a7d36a04d9ffaf77b7962e63535a2fa"
        }

        Otherwise fieldDetails is exactly the same as what was downloaded
        """

        response = table.get_item(
            Key={
                "pk": f"project_{self.project_id}",
                "sk": f"field_{self.page_name}_{field_index}" 
            }
        )

        existing_field = response.get('Item')

        try:
            default_field = self.default_fields[field_index-1]
        except IndexError:
            default_field = None


        if existing_field:
            default_values = existing_field
        elif default_field:
            default_values = default_field
            # don't try to change the field type if a default exists
            if field_type != default_field['type']:
                raise Exception('The field type does not match the default')
        else:
            default_values = {}

        optional_args = {
            "title": title,
            "description": description,
            "editable": editable,
            "field_data": field_data
        }

        for key in optional_args.keys():
            if not optional_args[key]: 
                optional_args[key] = default_values.get(key)

     
        print(optional_args)

        table.put_item(
            Item={
                "pk": f"project_{self.project_id}",
                "sk": f"field_{self.page_name}_{field_index}",
                "id": str(field_index),
                "title": optional_args['title'],
                "description": optional_args['description'],
                "type": field_type,
                "editable": optional_args['editable'],
                "fieldDetails": optional_args['field_data']
                
            }
        )


    def write_document_field(self, field_index, document_did, title=None, description=None, editable=None):

        field_data = {
            "documentDid": document_did 
        }

        self.write_field(
            field_index=field_index, 
            field_type='file', 
            field_data=field_data, 
            title=title, 
            description=description, 
            editable=editable
        )

            








