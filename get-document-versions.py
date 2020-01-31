import boto3
import json
import os
import requests

from modules import auth

def lambda_handler(event, context):

    api_id = os.environ["FOUNDATIONS_API_ID"]
    sp_did = os.environ["SP_DID"]
    api_stage = os.environ["FOUNDATIONS_API_STAGE"]
    document_did = event["path"]["document_did"]

    foundations_jwt = auth.get_foundations_jwt(sp_did)

    api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{document_did}/versions"

    params = {}

    response = requests.get(
        api_url,
        params=params,
        headers={'Authorization': foundations_jwt}
    )

    documents = json.loads(response.content.decode('utf-8'))['body']

    print(documents)
    
    return {
        "statusCode": 200,
        "body": documents
    }


if __name__ == '__main__':

    event = {
        "path": {
            "document_did": "did:fnds:b8349b4faeaa271333989c6c0e40f945d1d573d742eb0b5b909d0e330bc85bd7"
        }
    }

    lambda_handler(event,{})
        

        
