import boto3
import json
import os
from modules import project
from modules import errors
from modules import role
from modules import user
from urllib.parse import unquote

from modules import log
from modules.log import logger

try:
    stage_log_level = os.environ['PRIND_LOG_LEVEL']
except (NameError, KeyError):
    stage_log_level = 'CRITICAL'

print('stage_log_level:', stage_log_level)

# set the log level
log.set_logging_level(stage_log_level)


def lambda_handler(event, context):

    try:

        resource_path = event['requestPath']
        http_method = event['method']

        authenticating_username = event['cognitoPoolClaims']['sub']

        # list projects
        if http_method == "GET" and resource_path.endswith("list"):

            projects = project.list_all_projects()

            return_body = projects
            status_code = 200


        # get project members
        elif http_method == "GET" and resource_path.endswith("members"):

            this_project = project.Project(event['path']['project_id'])

            if not this_project.user_in_roles(authenticating_username, ["*"]):
                raise errors.InsufficientPermission("You do not have permission to view the members of this project")

            project_roles = this_project.get_roles()

            returned_output = []

            for project_role in project_roles:

                this_role = role.Role(project_role['roleId'])
                this_user = user.User(project_role['username'])

                try:
                    user_did  = this_user.get_did()
                except errors.DIDNotFound:
                    user_did = None

                list_item = {
                  "username": this_user.username,
                  "foundationsID": user_did,
                  "emailAddress": this_user.email_address,
                  "firstName": this_user.first_name,
                  "lastName": this_user.last_name,
                  "roleID": this_role.role_id,
                  "roleName": this_role.role_name
                }

                returned_output.append(list_item)

            return_body = returned_output
            status_code = 200

        # get-project
        elif http_method == "GET":
            
            this_project = project.Project(unquote(event['path']['project_id']))

            if not this_project.user_in_roles(authenticating_username, ["*"]):
                raise errors.InsufficientPermission("You do not have permission to view the details of this project")

            return_body = {
                "projectId": this_project.project_id,
                "projectName": this_project.project_name,
                "projectDescription": this_project.project_description,
                "projectReference": this_project.project_reference,
                "projectAddressLine1": this_project.site_address.get("projectAddressLine1"),
                "projectAddressLine2": this_project.site_address.get("projectAddressLine2"),
                "projectAddressLine3": this_project.site_address.get("projectAddressLine3"),
                "projectAddressTown": this_project.site_address.get("projectAddressTown"),
                "projectAddressRegion": this_project.site_address.get("projectAddressRegion"),
                "projectAddressPostalCode": this_project.site_address.get("projectAddressPostalCode"),
                "projectAddressCountry": this_project.site_address.get("projectAddressCountry")
            }

            status_code = 200

        # create project
        elif http_method == "POST" and resource_path.endswith("create"):

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
                project_creator=authenticating_username,
                project_description=event["body"].get('projectDescription'),
                project_reference=event["body"].get('projectReference'),
                site_address=site_address,
            )

            return_body = project_dict
            status_code = 201

        # update project
        elif http_method == "POST" and resource_path.endswith("update"):
            
            this_project = project.Project(unquote(event['path']['project_id']))

            if not this_project.user_in_roles(authenticating_username, ["*"]):
                raise errors.InsufficientPermission("You do not have permission to update this project")

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
                project_reference=event["body"].get('projectReference'),
                site_address=site_address
            )

            return_body = "completed"
            status_code = 201

        # invite member
        elif http_method == "POST" and resource_path.endswith("invite-member"):

            body = event['body']
            this_project = project.Project(unquote(event['path']['project_id']))

            if not this_project.user_in_roles(authenticating_username, ["*"]):
                raise errors.InsufficientPermission("You do not have permission to invite members to this project")
   
            this_project.invite_user(
                requesting_user_name=authenticating_username,
                invitee_email=event['body']['emailAddress'],
                role_id=event['body']['roleId']
            )

            return_body = "completed"
            status_code = 201

        # remove member
        elif http_method == "POST" and resource_path.endswith("remove-member"):

            print("running remove-member")

            body = event['body']
            this_project = project.Project(unquote(event['path']['project_id']))

            if not this_project.user_in_roles(authenticating_username, ["*"]):
                raise errors.InsufficientPermission("You do not have permission to remove members from this project")

            this_project.remove_user(
                requesting_user_name=authenticating_username,
                user_to_remove=event['body']['username']
            )

            return_body = "completed"
            status_code = 201

        # respond to invitation
        elif http_method == "POST" and resource_path.endswith("respond-to-invitation"):

            this_project = project.Project(unquote(event['path']['project_id']))

            this_project.respond_to_invitation(
                username=authenticating_username,
                accepted=event['body']['accepted']
            )

            return_body = "completed"
            status_code = 201

        # respond to invitation
        elif http_method == "POST" and resource_path.endswith("delete"):

            this_project = project.Project(unquote(event['path']['project_id']))

            if not this_project.user_in_roles(authenticating_username, ["client", "creator"]):
                raise errors.InsufficientPermission("You do not have permission to remove members from this project")

            this_project.delete()

            return_body = "completed"
            status_code = 200

        else:
            return_body = "invalid path"
            status_code = 400


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
        "statusCode": status_code,
        "body": return_body
    }
        
if __name__ == '__main__':

    
    event = {
        "list-projects": {
            "requestPath": "/project/list",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub": "6a628546-9b4e-4c43-96a4-4e30c3c37511"
            },
            "path": {}
        },        
        "get-project": {
            "requestPath": "/project/TestProjectInTheNewFormat2020-03-03",
            "method": "GET", 
            "cognitoPoolClaims": {
                "sub": "6a628546-9b4e-4c43-96a4-4e30c3c37511"
            },
            "path": {
                "project_id": "TestProjectInTheNewFormat2020-03-03"
            }
        },
        "create-project": { 
            "requestPath": "/project/create",
            "method": "POST",
            "cognitoPoolClaims": {
                "sub": "6a628546-9b4e-4c43-96a4-4e30c3c37511"
            },
            "body": {
               "projectName": "Test Project 10",
               "projectAddressLine1": "Test",
               "projectAddressLine2": "Test",
               "projectAddressLine3": "Test",
               "projectAddressTown": "Test",
               "projectAddressRegion": "Test",
               "projectAddressPostalCode": "AB12 3CD",
               "projectAddressCountry": "Test",
               "projectDescription": "This is a non-descript description",
               "projectReference": "123456"
            }
        },
        "update-project": { 
            "requestPath": "/project/TestProject2020-02-27/update",
            "method": "POST",
            "cognitoPoolClaims": {
                "sub": "6a628546-9b4e-4c43-96a4-4e30c3c37511"
            },
            "path": {
                "project_id": "TestProject2020-02-27"
            },
            "body": {
               # "projectName": "Test Project 2",
               # "projectAddressLine1": "Test",
               # "projectAddressLine2": "Test",
               # "projectAddressLine3": "Test",
               # "projectAddressTown": "TestTown",
               # "projectAddressRegion": "Test",
               # "projectAddressPostalCode": "AB12 3CD",
               # "projectAddressCountry": "Test",
               "projectReference": "12345555",
               # "projectDescription": "This is a non-descript description (updated)"
            }
        },
        "get-project-members": {
            "requestPath": "/project/TestProject2020-02-18/members",
            "method": "GET",
            "cognitoPoolClaims": {
                "sub": "6a628546-9b4e-4c43-96a4-4e30c3c37511"
            },"path": {
                "project_id": "ProjectNumberFive"
            }
        },
        "invite-project-member": {
            "requestPath": "/project/TestProject2020-02-18/invite-member",
            "method": "POST",
            "path": {
                "project_id": "ProjectNumberFour"
            },
            "cognitoPoolClaims": {
                "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
            },
            "body": {
                "emailAddress": "mr.simon.hunt+test17@gmail.com",
                "roleId": "projectConsultant"
            }
        },
        "remove-project-member": {
            "requestPath": "/project/ProjectNumberFour/remove-member",
            "method": "POST",
            "path": {
                "project_id": "ProjectNumberFour"
            },
            "cognitoPoolClaims": {
                "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
            },
            "body": {
                "username": "f9c255cb-a42b-4359-a8bd-2ebec5dfa2fa"
            }
        },
        "respond-to-invitation": {
            "requestPath": "/project/TestProject2020-02-18/respond-to-invitation",
            "method": "POST",
            "path": {
                "project_id": "ProjectNumberFour"
            },
            "cognitoPoolClaims": {
                "sub": "f9c255cb-a42b-4359-a8bd-2ebec5dfa2fa"
            },
            "body": {
                "accepted": True
            }
        },
        "delete-project": {
            "requestPath": "/project/TestProject2020-02-18/delete",
            "method": "POST",
            "path": {
                "project_id": "ProjectNumberFour"
            },
            "cognitoPoolClaims": {
                "sub": "f9c255cb-a42b-4359-a8bd-2ebec5dfa2fa"
            }
        }
    }

    print(lambda_handler(event["create-project"], {}))