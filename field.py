import boto3
import json
import os

from modules import errors
from modules import page

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr
from urllib.parse import unquote

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):

    try:

        project_id = unquote(event['path']['project_id'])
        page_name = unquote(event['path']['page'])
        field_index = event['path']['field_index']

        field_data = event['body']['fieldData']
        title = event['body']['title']
        description = event['body']['description'] 
        field_type = event['body']['type']
        editable = event['body']['editable']

        this_page = page.Page(page=page_name, project_id=project_id)

        this_page.write_field(
            field_index=field_index, 
            field_data=field_data, 
            title=title, 
            description=description, 
            field_type=field_type, 
            editable=editable
        )

    # catch any application errors
    except:
        raise

    # except errors.ApplicationError as error:
    #     return {
    #         'statusCode': 400,
    #         "Error": error.get_error_dict()
    #     }
    # # catch unhandled exceptions
    # except Exception as e:
        
    #     # logger.error(log.logging.exception("message"))

    #     return {
    #         'statusCode': 500,
    #         'Error': errors.UnhandledException(context.log_group_name, context.log_stream_name, context.aws_request_id).get_error_dict()
    #     }

    
    return {
        "statusCode": 200,
        "body": "completed"
    }


if __name__ == '__main__':

    event = {
        "path": {
            "project_id": "ProjectNumberFour",
            "page": "feasibility",
            "field_index": 2
        },
        "body": {
            "fieldData": {
              "dropdownValue": "No",
              "textboxValue": ".",
              "dropdownOptions": [
                {
                  "id": "1",
                  "name": "Yes"
                },
                {
                  "id": "2",
                  "name": "No"
                }
              ],
              "optionOpensTextBox": "Yes"
            },
            "title": "This is a test drop-down box", 
            "description": "This is a test field",
            "type": "dropdown",
            "editable": True
        }
    }

    print(lambda_handler(event, {}))