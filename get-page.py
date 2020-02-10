import boto3
import json
import os

from modules import errors
from modules import page

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):

    try:

        project_id = event['path']['project_id']
        page_name = event['path']['page']

        this_page = page.Page(page=page_name, project_id=project_id)

        page_fields = this_page.get_resultant_fields()

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
        "body": page_fields
    }


if __name__ == '__main__':

    event = {
        "path": {
            "project_id": "ProjectNumberFour",
            "page": "inception"
        }
    }

    print(lambda_handler(event, {}))