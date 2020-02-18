import boto3
import json
import os
from modules import project
from modules import errors
from urllib.parse import unquote


def lambda_handler(event, context):

    try:

        this_project = project.Project(unquote(event['path']['project_id']))

        return_dict = {
            "Id": this_project.project_id,
            "name": this_project.project_name,
            "description": this_project.project_description,
            "siteAddress": this_project.site_address,
        }

    # catch any application errors
    except errors.ApplicationError as error:
        return {
            'statusCode': 400,
            "Error": error.get_error_dict()
        }
    # catch unhandled exceptions
    except Exception as e:
        
        # logger.error(log.logging.exception("message"))

        return {
            'statusCode': 500,
            'Error': errors.UnhandledException(context.log_group_name, context.log_stream_name, context.aws_request_id).get_error_dict()
        }

    
    return {
        "statusCode": 200,
        "body": return_dict
    }
        
if __name__ == '__main__':

    event = { 
        "cognitoPoolClaims": {
            "sub": "6a628546-9b4e-4c43-96a4-4e30c3c37511"
        },
        "path": {
            "project_id": "TestProject2020-02-18"
        }
    }

    print(lambda_handler(event, {}))
        
