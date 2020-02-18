import boto3
import json
import os
from modules import project
from modules import errors

from urllib.parse import unquote


def lambda_handler(event, context):

    try:

        this_project = project.Project(unquote(event['path']['project_id']))

        site_address = {
           "projectAddressLine1": event["body"].get("projectAddressLine1"),
           "projectAddressLine2": event["body"].get("projectAddressLine2"),
           "projectAddressLine3": event["body"].get("projectAddressLine3"),
           "projectAddressTown": event["body"].get("projectAddressTown"),
           "projectAddressRegion": event["body"].get("projectAddressRegion"),
           "projectAddressPostalCode": event["body"].get("projectAddressPostalCode"),
           "projectAddressCountry": event["body"].get("projectAddressCountry")
        }

        print("description is", event["body"].get('projectDescription'))

        this_project.update(
            project_name=event["body"].get('projectName'),
            project_description=event["body"].get('projectDescription'),
            site_address=site_address
        )

    # catch any application errors
    except errors.ApplicationError as error:
        return {
            'statusCode': 400,
            "Error": error.get_error_dict()
        }
    # catch unhandled exceptions
    # except Exception as e:
        
    #     # logger.error(log.logging.exception("message"))

    #     return {
    #         'statusCode': 500,
    #         'Error': errors.UnhandledException(context.log_group_name, context.log_stream_name, context.aws_request_id).get_error_dict()
    #     }

    
    return {
        "statusCode": 201,
        "body": "completed"
    }


if __name__ == '__main__':

    event = { 
        "cognitoPoolClaims": {
            "sub": "6a628546-9b4e-4c43-96a4-4e30c3c37511"
        },
        "path": {
            "project_id": "TestProject2020-02-18"
        },
        "body": {
           "projectName": "Test Project 2",
           "projectAddressLine1": "Test",
           "projectAddressLine2": "Test",
           "projectAddressLine3": "Test",
           "projectAddressTown": "TestTown",
           "projectAddressRegion": "Test",
           "projectAddressPostalCode": "AB12 3CD",
           "projectAddressCountry": "Test",
           "projectDescription": "This is a non-descript description (updated)"
        }
    }

    print(lambda_handler(event, {}))

        
