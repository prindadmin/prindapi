import boto3
import json
import os
from modules import project
from modules import errors

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):

    try:

        this_project = project.Project(event['path']['project_id'])
        page = event['path']['page']

        # get default page fields
        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"defaultField_{page}")
        )

        try:
            default_fields = response["Items"]
        except KeyError:
            default_fields = []

        print(default_fields)



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

    
    # return {
    #     "statusCode": 200,
    #     "body": "done"
    # }

if __name__ == '__main__':

    event = {
        "path": {
            "project_id": "ProjectNumberFour",
            "page": "construction"
        }
    }

    lambda_handler(event, {})