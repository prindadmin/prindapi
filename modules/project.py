import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors
from modules import user
from modules import role



# If logger hasn"t been set up by a calling function, set it here

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
        self.site_address = item['siteAddress']
        self.occupied_during_works = item['occupiedDuringWorks']
        self.workplace_when_completed = item['workplaceWhenCompleted']

    def get_user_role(self, user_name):


        response = table.get_item(
            Key={
                "pk": f"user_{user_name}",
                "sk": f"role_{self.project_id}"
            }
        )

        try:
            return response['Item']['data']
        except:
            return None

    def user_has_permission(self, user_name):

        project_owner = self.get_owner()
        print(project_owner)

        if project_owner == user_name:
            return True
        elif get_user_role(user_name):
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

        return project_roles


    def add_user_role(
            self,
            requesting_user_name,
            user_to_add,
            role_id
        ):

        # check if requesting user is the owner of the project, or has a role on the project
        if not self.user_has_permission(requesting_user_name):
           raise errors.InsufficientPermission("Requesting user does not have permission to add a role to this project") 

        # check that role is assignable
        assigned_role = role.Role(role_id)

        table.put_item(
            Item={    
                "pk": f"user_{user_to_add}",
                "sk": f"role_{self.project_id}",
                "data": assigned_role.role_id 
            }
        )

    def get_owner(self):

        response = table.query(
            IndexName="GSI1",
            KeyConditionExpression=Key("sk").eq(f"projectOwner_{self.project_id}")
        )

        item = response['Items'][0]
        owner = item['pk'].split('user_')[1]

        return owner


    def update(
            self,
            project_name=None,
            project_description=None,
            site_address=None,
            occupied_during_works=None,
            workplace_when_completed=None
        ):

        if project_name == None:
            project_name = self.project_name
        if project_description == None:
            project_description = self.description
        if site_address == None:
            site_address = self.site_address
        if occupied_during_works == None:
            occupied_during_works = self.occupied_during_works
        if workplace_when_completed == None:
            workplace_when_completed = self.workplace_when_completed

        table.put_item(
            Item={    
                "pk": f"project_{self.project_id}",
                "sk": "project",
                "data": self.project_id, 
                "displayName": project_name,
                "description": project_description,
                "siteAddress": site_address,
                "occupiedDuringWorks": occupied_during_works,
                "workplaceWhenCompleted": workplace_when_completed
            }
        )

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
        site_address,
        occupied_during_works=False,
        workplace_when_completed=False
    ):

    project_id = camelize(project_name)

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
                "siteAddress": site_address,
                "occupiedDuringWorks": occupied_during_works,
                "workplaceWhenCompleted": workplace_when_completed
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
    else:
        raise errors.ProjectAlreadyExists(f"A project with the ID {project_id} already exists")


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

    return projects


if __name__ == "__main__":

    pass
    
    #get_project("TestProject")
    #create_project("Test Project", "This is a test project", "West Street, Farnham, Surrey")



