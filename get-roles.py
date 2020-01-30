import boto3
import json
import os
from modules import role



def lambda_handler(event, context):



    roles = role.get_all_roles()

    
    return {
        "statusCode": 200,
        "body": roles
    }
        

        
