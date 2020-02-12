import boto3
import json
import os
from modules import project
from modules import errors
from modules import user
from modules import role


def lambda_handler(event, context):

    try:

        this_project = project.Project(event['path']['project_id'])

        project_roles = this_project.get_roles()

        returned_output = []

        for project_role in project_roles:

            this_role = role.Role(project_role['roleId'])
            this_user = user.User(project_role['username'])

            list_item = {
              "username": this_user.username,
              "foundationsID": this_user.get_did(),
              "emailAddress": this_user.email_address,
              "firstName": this_user.first_name,
              "lastName": this_user.last_name,
              "roleID": this_role.role_id,
              "roleName": this_role.role_name
            }

            returned_output.append(list_item)

    except:
        raise

    # # catch any application errors
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
        "body": returned_output
    }

if __name__ == '__main__':

    event = {
        # "cognitoPoolClaims": {
        #     "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
        # },
        "path": {
            "project_id": "ProjectNumberFive"
        }
    }

    print(lambda_handler(event, {}))
        

        
