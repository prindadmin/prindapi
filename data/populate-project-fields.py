import boto3
import json
import os

stage = input("enter stage: ")

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(f'prind-{stage}')

current_directory = os.path.dirname(os.path.realpath(__file__))

files = [
    "project-fields-construction.json",
    "project-fields-design.json",
    "project-fields-feasibility.json",
    "project-fields-handover.json",
    "project-fields-inception.json",
    "project-fields-occupation.json",
    "project-fields-tender.json"
]

for file in files:
    print('loading file', file)
    
    project_fields_file = open(f"{current_directory}/{file}")
    project_fields = project_fields_file.read()
    project_fields_file.close()

    project_fields = json.loads(project_fields)

    for field in project_fields:

        table.put_item(
            Item=field
        )