import boto3
import json
import os
from modules import project
from modules import errors
from urllib.parse import unquote


def lambda_handler(event, context):

    try:

        resource_path = event['requestPath']
        http_method = event['method']

        print(event)

        # get-project
        if http_method == "GET":
            
            this_project = project.Project(unquote(event['path']['project_id']))

            return_body = {
                "projectId": this_project.project_id,
                "projectName": this_project.project_name,
                "description": this_project.project_description,
                "siteAddress": this_project.site_address,
            }

            status_code = 200

        # create project
        elif http_method == "POST" and resource_path.endswith("create"):

            authorizing_username = event['cognitoPoolClaims']['sub']

            site_address = {
               "projectAddressLine1": event["body"].get("projectAddressLine1"),
               "projectAddressLine2": event["body"].get("projectAddressLine2"),
               "projectAddressLine3": event["body"].get("projectAddressLine3"),
               "projectAddressTown": event["body"].get("projectAddressTown"),
               "projectAddressRegion": event["body"].get("projectAddressRegion"),
               "projectAddressPostalCode": event["body"].get("projectAddressPostalCode"),
               "projectAddressCountry": event["body"].get("projectAddressCountry")
            }

            
            project_dict = project.create_project(
                project_name=event["body"].get('projectName'),
                project_creator=authorizing_username,
                project_description=event["body"].get('projectDescription'),
                site_address=site_address,
            )

            return_body = project_dict
            status_code = 201

        # update project
        elif http_method == "POST" and resource_path.endswith("update"):
            
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

            return_body = "completed"
            status_code = 201


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
        "statusCode": status_code,
        "body": return_body
    }
        
if __name__ == '__main__':

    # get project
    # event = {
    #     "requestPath": "/project/ProjectNumberFour",
    #     "method": "get", 
    #     "cognitoPoolClaims": {
    #         "sub": "6a628546-9b4e-4c43-96a4-4e30c3c37511"
    #     },
    #     "path": {
    #         "project_id": "TestProject2020-02-18"
    #     }
    # }


    # create project
    # event = { 
    #     "requestPath": "/project/create",
    #     "method": "post",
    #     "cognitoPoolClaims": {
    #         "sub": "6a628546-9b4e-4c43-96a4-4e30c3c37511"
    #     },
    #     "body": {
    #        "projectName": "Test Project",
    #        "projectAddressLine1": "Test",
    #        "projectAddressLine2": "Test",
    #        "projectAddressLine3": "Test",
    #        "projectAddressTown": "Test",
    #        "projectAddressRegion": "Test",
    #        "projectAddressPostalCode": "AB12 3CD",
    #        "projectAddressCountry": "Test",
    #        "projectDescription": "This is a non-descript description"
    #     }
    # }

    # update project
    event = { 
        "requestPath": "/project/TestProject2020-02-18/update",
        "method": "post",
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