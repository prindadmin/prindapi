import boto3
import json
import os
from modules import role
from modules import errors



def lambda_handler(event, context):


    try:

        roles = role.list_all_roles()
    
    except errors.ApplicationError as error:
        return {
            'statusCode': 400,
            "Error": error.get_error_dict()
        }

    return {
        "statusCode": 200,
        "body": roles
    }
        

        
