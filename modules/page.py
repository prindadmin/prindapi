import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors
from modules import project
from modules import document
from modules import log

# If logger hasn"t been set up by a calling function, set it here
try:
    logger
except:
    from modules.log import logger
    log.set_logging_level()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

class Page():

    def __init__(self, page, project_id):

        project.Project.__init__(self, project_id=project_id)

        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"defaultField_{page}")
        )

        items = response['Items']

        if items == []:
            raise errors.PageNotFound(f"A page with name {page} was not found.")

        for item in items:
            item.pop("sk", None)
            item.pop("pk", None)

        self.page_name = page
        self.project_id = project_id
        self.default_fields = items

        logger.debug(log.function_end_output(locals()))

    def get_highest_field_index(self):

        number_of_default_fields = len(self.default_fields)

        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"project_{self.project_id}") & Key("sk").begins_with(f"field_{self.page_name}")
        )

        populated_fields = response['Items']

        highest_populated_index = max([int(field['id']) for field in populated_fields], default=0)

        return max([number_of_default_fields, int(highest_populated_index)])


    def get_populated_fields(self):

        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"project_{self.project_id}") & Key("sk").begins_with(f"field_{self.page_name}")
        )

        items = response['Items']

        populated_fields = {}
        
        for item in items:
            item.pop('pk')
            item.pop('sk')           
            field_index = item["id"]

            # Add any file details
            if item['type'] == 'file':
                try:
                    this_document = document.Document(
                        project_id=self.project_id, 
                        page=self.page_name, 
                        field_index=field_index
                    )
                except errors.DocumentNotFound:
                    logger.info(f"The field {self.project_id}/{self.page_name}/{field_index} didn't contain a file")
                    item['fileDetails'] = []
                else:
                    item['fileDetails'] = this_document.get_all_info()
            
            populated_fields[str(field_index)] = item

        logger.debug(log.function_end_output(locals()))  

        return populated_fields

    def get_resultant_fields(self):

        populated_fields = self.get_populated_fields()
        resultant_fields = []

        # resultant pre-defined fields
        for default in self.default_fields:
            try:
                value_for_this_index = populated_fields[default['id']]
            except KeyError:
                resultant_fields.append(default)
            else:
                resultant_fields.append(value_for_this_index)

        populated_fields_list = []

        for id in sorted(populated_fields, key=int):
            populated_fields_list.append(populated_fields[id])

        # add any additional custom fields
        custom_fields = [f for f in populated_fields_list if f not in resultant_fields]

        resultant_fields = resultant_fields + custom_fields

        logger.debug(log.function_end_output(locals()))  

        return resultant_fields

    def write_field(self, field_index, field_type, field_data=None, title=None, description=None, editable=None):

        response = table.get_item(
            Key={
                "pk": f"project_{self.project_id}",
                "sk": f"field_{self.page_name}_{field_index}" 
            }
        )


        existing_field = response.get('Item')

        logger.info(f"existing_field is: {existing_field}")

        try:
            default_field = self.default_fields[int(field_index)-1]
        except IndexError:
            default_field = None


        if existing_field:
            default_values = existing_field
        elif default_field:
            default_values = default_field
            # don't try to change the field type if a default exists
            if field_type != default_field['type']:
                raise errors.InvalidFieldType('The field type does not match the default')
        else:
            default_values = {}

        optional_args = {
            "title": title,
            "description": description,
            "editable": editable,
            "fieldDetails": field_data
        }

        for arg in optional_args.keys():
            if optional_args[arg] == None:
                try:
                    optional_args[arg] = default_values[arg]
                except KeyError:
                    raise errors.MissingRequiredFields(f"{arg} does not have a value for this field")
     
        logger.info(f"optional_args are: {optional_args}")

        table.put_item(
            Item={
                "pk": f"project_{self.project_id}",
                "sk": f"field_{self.page_name}_{field_index}",
                "id": str(field_index),
                "title": optional_args['title'],
                "description": optional_args['description'],
                "type": field_type,
                "editable": optional_args['editable'],
                "fieldDetails": optional_args['fieldDetails']
                
            }
        )

        logger.debug(log.function_end_output(locals()))  
