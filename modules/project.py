import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors



# If logger hasn"t been set up by a calling function, set it here

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


def camelize(string):
    from re import split
    return ''.join(a.capitalize() for a in split('([^a-zA-Z0-9])', string)
       if a.isalnum())

def create_project(
        project_name,
        project_description,
        site_address,
        occupied_during_works=False,
        workplace_when_complete=False
    ):

    project_name_camelcase = camelize(project_name)

    table.put_item(
        Item={    
            "pk": f"project_{project_name_camelcase}",
            "sk": "project", 
            "displayName": project_name,
            "description": project_description,
            "siteAddress": site_address,
            "occupiedDuringWorks": occupied_during_works,
            "workplaceWhenCompleted": workplace_when_complete
        }
    )

def get_project(project_id):

    response = table.get_item(
        Key={
            "pk": f"project_{project_id}",
            "sk": "project"
        }
    )

    try:
        item = response['Item']
    except KeyError:
        return None

    return item




if __name__ == "__main__":

    pass
    
    #get_project("TestProject")
    #create_project("Test Project", "This is a test project", "West Street, Farnham, Surrey")



