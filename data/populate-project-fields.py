import boto3
import json
import os

stage = input("enter stage: ")

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(f'prind-{stage}')

current_directory = os.path.dirname(os.path.realpath(__file__))

files = [
    "CDM2015Project/project-fields-construction.json",
    "CDM2015Project/project-fields-design.json",
    "CDM2015Project/project-fields-feasibility.json",
    "CDM2015Project/project-fields-handover.json",
    "CDM2015Project/project-fields-inception.json",
    "CDM2015Project/project-fields-occupation.json",
    "CDM2015Project/project-fields-tender.json",
    "DHSFProject/project-fields-occupation.json",
]

for file in files:
    print('loading file', file)
    
    project_fields_file = open(f"{current_directory}/project-fields/{file}")
    project_fields = project_fields_file.read()
    project_fields_file.close()

    project_fields = json.loads(project_fields)

    for field in project_fields:

        table.put_item(
            Item=field
        )