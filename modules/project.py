import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from datetime import date

from modules import errors
from modules import user
from modules import role
from modules import mail
from modules import log

# If logger hasn"t been set up by a calling function, set it here
try:
    logger
except:
    from modules.log import logger
    log.set_logging_level()

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

class Project():

    def __init__(self, project_id):

        # logger.info(log.function_start_output())

        response = table.get_item(
            Key={
                "pk": f"project_{project_id}",
                "sk": "project"
            }
        )

        try:
            item = response['Item']
        except KeyError:
            raise errors.ProjectNotFound(f"A project with ID {project_id} was not found.")

        self.project_id = project_id
        self.project_name = item['displayName']
        self.project_description = item['description']
        self.project_reference = item.get('reference')
        self.site_address = item['siteAddress']

        logger.debug(log.function_end_output(locals()))  

    def get_user_role(self, username):


        response = table.get_item(
            Key={
                "pk": f"user_{username}",
                "sk": f"role_{self.project_id}"
            }
        )

        logger.debug(log.function_end_output(locals()))  

        try:
            return response['Item']['data']
        except:
            return None

    def user_has_permission(self, username):

        project_owner = self.get_owner()

        logger.debug(project_owner)

        logger.debug(log.function_end_output(locals()))  

        if project_owner == username:
            return True
        elif self.get_user_role(username):
            return True
        else:
           return False

    def user_in_roles(self, username, allowed_roles=["*"]):

        if not isinstance(allowed_roles, list):
            raise Exception('allowed_roles should be a list')

        users_role = self.get_user_role(username)

        # if ["*"] is specified, return true if a role is returned
        if allowed_roles == ["*"]:
            if users_role:
                return True
            else:
                return False

        # otherwise return true only if the role is in the list
        if users_role in allowed_roles:
            return True
        else:
            return False

    def get_roles(self):
        
        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("sk").eq(f"role_{self.project_id}")
        )

        items = response['Items']

        project_roles = []

        for item in items:

            item["username"] = item.pop("pk").split("user_")[1]
            item.pop("sk")
            item["roleId"] = item.pop("data")

            project_roles.append(item)

        logger.debug(log.function_end_output(locals()))  

        return project_roles


    def add_user_role(
            self,
            requesting_user_name,
            user_to_add,
            role_id
        ):

        # check that role is assignable
        assigned_role = role.Role(role_id)

        table.put_item(
            Item={    
                "pk": f"user_{user_to_add}",
                "sk": f"role_{self.project_id}",
                "data": assigned_role.role_id,
                "dateJoined": str(int(time.time()))
            }
        )

        logger.debug(log.function_end_output(locals()))  

    def invite_user(
            self,
            requesting_user_name,
            invitee_email,
            role_id
        ):

        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression=(Key("sk").eq("userDetails_emailAddress") & Key("data").eq(invitee_email))
        )

        if len(response["Items"]) > 0:
            item = response["Items"][0]
            user_to_add = item["pk"].split("user_")[1]
        else:
            raise errors.UserNotFound(f"user with email address {invitee_email} not found")

        print("user_to_add", user_to_add)

        # check that role is assignable
        assigned_role = role.Role(role_id)

        table.put_item(
            Item={    
                "pk": f"user_{user_to_add}",
                "sk": f"roleInvitation_{self.project_id}",
                "data": assigned_role.role_id ,
                "requestedBy": requesting_user_name,
                "requestedAt": str(int(time.time()))
            }
        )

        user_to_add_obj = user.User(user_to_add)

        template_data = {
            "firstName": user_to_add_obj.first_name,
            "projectName": self.project_name,
            "roleName": assigned_role.role_name
        }

        mail.send_email(user_to_add_obj.email_address, "project-invitation", template_data)

        logger.debug(log.function_end_output(locals()))

    def remove_user(
            self,
            requesting_user_name,
            user_to_remove
        ):

        # remove any invitations
        table.delete_item(
            Key={    
                "pk": f"user_{user_to_remove}",
                "sk": f"roleInvitation_{self.project_id}",
            }
        )

        # remove any memberships
        table.delete_item(
            Key={    
                "pk": f"user_{user_to_remove}",
                "sk": f"role_{self.project_id}",
            }
        )



    def respond_to_invitation(
            self,
            username,
            accepted=True
        ):
        
        # get roleInvitation and archive it as roleIvitationResponse
        response = table.delete_item(
            Key={
                "pk": f"user_{username}",
                "sk": f"roleInvitation_{self.project_id}"
            },
            ReturnValues="ALL_OLD"
        )

        try:
            old_item = response["Attributes"]
        except KeyError:
            raise errors.InvitationNotFound(f"A Project Invitation for {username} and {self.project_id} was not found")
        # old_item = {'sk': 'roleInvitation_ProjectNumberFour', 'requestedBy': '778bd486-4684-482b-9565-1c2a51367b8c', 'pk': 'user_d7b4396c-e7d5-4190-b449-6d4cdf976473', 'data': 'projectConsultant', 'requestedAt': '1582041857'}
        new_item = old_item.copy()

        new_item['sk'] = f"roleInvitationResponse_{self.project_id}"
        new_item['accepted'] = accepted
        new_item['respondedAt'] = str(int(time.time()))

        table.put_item(
            Item=new_item
        )

        from_username = old_item['requestedBy']
        role_id = old_item['data']

        # add the user role, if it was accepted
        if accepted:
            self.add_user_role(
                requesting_user_name=from_username,
                user_to_add=username,
                role_id=role_id
            )

        # send email to the inviter with the response
        from_user_obj = user.User(username)
        to_user_obj = user.User(from_username)

        template_data = {
            "inviterFirstName": to_user_obj.first_name,
            "inviteeFirstName": from_user_obj.first_name,
            "inviteeLastName": from_user_obj.last_name,
            "response": "accepted" if accepted else "declined",
            "projectName": self.project_name
        }

        logger.debug(template_data)

        mail.send_email(to_user_obj.email_address, "project-invitation-response", template_data)

        logger.debug(log.function_end_output(locals()))  

    def get_owner(self):

        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("sk").eq(f"projectOwner_{self.project_id}")
        )

        item = response['Items'][0]
        owner = item['pk'].split('user_')[1]

        logger.debug(log.function_end_output(locals()))  

        return owner


    def update(
            self,
            project_name=None,
            project_description=None,
            project_reference=None,
            site_address=None
        ):

        if project_name == None:
            project_name = self.project_name
        if project_description == None:
            project_description = self.project_description
        if project_reference == None:
            project_reference = self.project_reference
        if site_address == None:
            site_address = self.site_address

        table.put_item(
            Item={    
                "pk": f"project_{self.project_id}",
                "sk": "project",
                "data": self.project_id, 
                "displayName": project_name,
                "description": project_description,
                "reference": project_reference,
                "siteAddress": site_address,
            }
        )

        logger.debug(log.function_end_output(locals()))  

def get_user_projects(username):

    response = table.query(
        KeyConditionExpression=Key("pk").eq(f"user_{username}") & Key("sk").begins_with("role_")
    )

    items = response.get('Items', [])

    project_roles = []

    for item in items:
        project_id = item.pop('sk').split('role_')[1]
        role_id = item.pop('data')
        item.pop('pk')
        item['projectId'] = project_id
        item['projectName'] = Project(project_id).project_name
        item['roleName'] = role.Role(role_id).role_name
        item['dateTime'] = item.pop('dateJoined', '0000000000')

        project_roles.append(item)


    response = table.query(
        KeyConditionExpression=Key("pk").eq(f"user_{username}") & Key("sk").begins_with("projectOwner_")
    )

    items = response.get('Items', [])

    project_ownerships = []

    for item in items:
        project_id = item.pop('sk').split('projectOwner_')[1]
        item.pop('pk')
        item.pop('data')
        item['projectId'] = project_id
        item['projectName'] = Project(project_id).project_name

        project_ownerships.append(item)

    logger.debug(log.function_end_output(locals()))  

    return {
        "projectOwner": project_ownerships,
        "projectRole": project_roles
    }


def camelize(string):
    from re import split
    return ''.join(a.capitalize() for a in split('([^a-zA-Z0-9])', string)
       if a.isalnum())



def create_project(
        project_name,
        project_creator,
        project_description,
        project_reference,
        site_address
    ):

    date_suffix = date.today().isoformat()

    project_id = camelize(project_name) + date_suffix

    project_owner = user.User(project_creator)

    # check if project exists before adding it
    try:
        project = Project(project_id)
    except errors.ProjectNotFound:
        table.put_item(
            Item={    
                "pk": f"project_{project_id}",
                "sk": "project",
                "data": project_id, 
                "displayName": project_name,
                "description": project_description,
                "reference": project_reference,
                "siteAddress": site_address,
            }
        )

        # add the creating user as the owner of the project
        table.put_item(
            Item={
                "pk": f"user_{project_owner.username}",
                "sk": f"projectOwner_{project_id}",
                "data": str(int(time.time()))
            }
        )

        table.put_item(
            Item={    
                "pk": f"user_{project_owner.username}",
                "sk": f"role_{project_id}",
                "data": "creator" 
            }
        )
    else:
        raise errors.ProjectAlreadyExists(f"A project with the ID {project_id} already exists")

    logger.debug(log.function_end_output(locals()))  

    return {
        "projectId": project_id,
        "projectName": project_name
    }


def list_all_projects():

    response = table.query(
        IndexName="GSI1",
        KeyConditionExpression=Key("sk").eq("project")
    )

    items = response['Items']

    projects = []

    for item in items:
        
        item['projectId'] = item.pop('pk').split('project_')[1]
        item.pop('sk')
        item['projectName'] = item.pop('data')
        
        projects.append(item)

    logger.debug(log.function_end_output(locals()))  

    return projects


if __name__ == "__main__":

    pass
    
    #get_project("TestProject")
    #create_project("Test Project", "This is a test project", "West Street, Farnham, Surrey")



