import boto3
import time
import json
import os
import requests
from datetime import datetime

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors
from modules import auth
from modules import user
from modules import did


# If logger hasn"t been set up by a calling function, set it here

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


api_id = os.environ["FOUNDATIONS_API_ID"]
sp_did = os.environ["SP_DID"]
api_stage = os.environ["FOUNDATIONS_API_STAGE"]
factom_explorer_domain = os.environ["FACTOM_EXPLORER_DOMAIN"]

foundations_jwt = auth.get_foundations_jwt(sp_did)

class Document():

    def __init__(self, document_did):

        # logger.info(log.function_start_output())

        response = table.get_item(
            Key={
                "pk": f"document_{document_did}",
                "sk": "document"
            }
        )

        try:
            item = response['Item']
        except KeyError:
            raise errors.DocumentNotFound(f"A document with DID {document_did} was not found.")

        self.document_did = document_did
        self.s3_bucket_name = item['s3BucketName']
        self.s3_key = item['s3Key']
        self.filename = item['filename']

    def get_current_version_number(self):

        response = table.get_item(
            Key={
                "pk": f"document_v0__{document_did}",
                "sk": "documentVersion"
            }
        )

        return response['Item']['versionNumber']

    def get_foundations_info(self):

        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{self.document_did}/versions"

        params = {}

        response = requests.get(
            api_url,
            params=params,
            headers={'Authorization': foundations_jwt}
        )

        versions = json.loads(response.content.decode('utf-8'))['body']

        return versions

    def get_version_signatures(self, version):

        api_url=f"https://{api_id}.execute-api.eu-west-1.amazonaws.com/{api_stage}/sp/document-did/{self.document_did}/version-signatures/{version}"

        params = {}

        response = requests.get(
            api_url,
            params=params,
            headers={'Authorization': foundations_jwt}
        )

        signatures = json.loads(response.content.decode('utf-8'))['body']

        return signatures

    def get_all_info(self):

        foundations_document = self.get_foundations_info()

        versions = foundations_document['documentVersions']

        latest_version = len(versions) - 1

        latest_version_signatures = self.get_version_signatures(latest_version)['signatures']

        for signing in latest_version_signatures:

            signing['signedBy'] = signing.pop('signingDid')
 
            try:     
                signing_username = did.Did(signing['signedBy']).get_cognito_username()
            except errors.DIDNotFound:
                signing_username = 'Unregistered User'

            signing['signerName'] = user.User(signing_username).name
            signed_at_unixtime = signing.pop('signedAt')
            signing['signatureDateTime'] = datetime.utcfromtimestamp(signed_at_unixtime).isoformat()
            entry_hash = signing.pop('entryHash')
            signing['proofLink'] = f"https://{factom_explorer_domain}/entry?hash={entry_hash}"

        for version in versions:

            created_at_unixtime = version.pop('versionCreatedAt')
            version['uploadedDateTime'] = datetime.utcfromtimestamp(created_at_unixtime).isoformat()
            version['hash'] = version.pop('documentHash')
            entry_hash = version.pop('entryHash')
            version['proofLink'] = f"https://{factom_explorer_domain}/entry?hash={entry_hash}"
            version['uploadedBy'] = "Someone"
            version['ver'] = version.pop('index')
            version.pop('versionNumber')

            this_version = int(version['ver'])

            if (this_version == 0 or this_version == latest_version):
                version['signatures'] = latest_version_signatures
            else:
                version['signatures'] = []


        print(versions)






    #     [
    #   {
    #     "ver": 0,
    #     "uploadName": "file-v002.txt",
    #     "uploadDateTime": "2020-01-30T12:04:59",
    #     "uploadedBy": "Jim Moriaty",
    #     "hash": "6c434ff047a8baff01375d4f744fd7508b68f36b19fa9111692504f6b2df9baf",
    #     "proofLink": "https://explorer.factoid.org/entry?hash=6c434ff047a8baff01375d4f744fd7508b68f36b19fa9111692504f6b2df9baf",
    #     "signatures": [
    #       {
    #         "signedBy": "did:did:74yw1upt9eeyy21sa3g4",
    #         "signerName": "Jim Moriaty",
    #         "signatureDateTime": "2020-01-30T13:52:08",
    #         "proofLink": "https://explorer.factoid.org/entry?hash=741f9d15ec73b9d2282a10956c946c24117ee69a7360cee0790d470c85f88d6b"
    #       },
    #       {
    #         "signedBy": "did:did:74yw1upt9eeyy21sa3g5",
    #         "signerName": "Irene Adler",
    #         "signatureDateTime": "2020-01-30T15:53:26",
    #         "proofLink": "https://explorer.factoid.org/entry?hash=4e52b2c5229244bec7517cd7505faca1d6fd0291a69b40d27f79cfb638f65ed5"
    #       }
    #     ]
    #   },
    #   {
    #     "ver": 1,
    #     "uploadName": "file-v001.txt",
    #     "uploadDateTime": "2020-01-29T12:04:59",
    #     "uploadedBy": "Jim Moriaty",
    #     "hash": "ee78b5ad676d1855fff856a2cfae44ca41e84aaebd9ecca20cc975ea0c1b8c21",
    #     "proofLink": "https://explorer.factoid.org/entry?hash=ee78b5ad676d1855fff856a2cfae44ca41e84aaebd9ecca20cc975ea0c1b8c21",
    #     "signatures": [
    #       {
    #         "signedBy": "did:did:74yw1upt9eeyy21sa3g4",
    #         "signerName": "Jim Moriaty",
    #         "signatureDateTime": "2020-01-29T13:52:08",
    #         "proofLink": "https://explorer.factoid.org/entry?hash=6f08b7c0820ba73f75f61af8176236c0575565d07827951eb52956e06d5e158f"
    #       }
    #     ]
    #   },
    #   {
    #     "ver": 2,
    #     "uploadName": "file-v002.txt",
    #     "uploadDateTime": "2020-01-30T12:04:59",
    #     "uploadedBy": "Jim Moriaty",
    #     "hash": "6c434ff047a8baff01375d4f744fd7508b68f36b19fa9111692504f6b2df9baf",
    #     "proofLink": "https://explorer.factoid.org/entry?hash=6c434ff047a8baff01375d4f744fd7508b68f36b19fa9111692504f6b2df9baf",
    #     "signatures": [
    #       {
    #         "signedBy": "did:did:74yw1upt9eeyy21sa3g4",
    #         "signerName": "Jim Moriaty",
    #         "signatureDateTime": "2020-01-30T13:52:08",
    #         "proofLink": "https://explorer.factoid.org/entry?hash=741f9d15ec73b9d2282a10956c946c24117ee69a7360cee0790d470c85f88d6b"
    #       },
    #       {
    #         "signedBy": "did:did:74yw1upt9eeyy21sa3g5",
    #         "signerName": "Irene Adler",
    #         "signatureDateTime": "2020-01-30T15:53:26",
    #         "proofLink": "https://explorer.factoid.org/entry?hash=4e52b2c5229244bec7517cd7505faca1d6fd0291a69b40d27f79cfb638f65ed5"
    #       }
    #     ]
    #   }
    # ]

        # {
        #   "documentHash": "74de57558ebeb1fa0f92d5c6d8f7e10bf36be4c14dc5afa9a323774b4dfda70a",
        #   "versionCreatedAt": 1580901112.0,
        #   "versionNumber": 3,
        #   "entryHash": "ad776d4d212988127c6bffe5be4070ded1a6588c757f5b0be0c40faed4562453",
        #   "index": "0"
        # },
        # {
        #   "createdByDid": "did:fctr:d85be1f5baa83fa83850d8b58731a7f7c8ba65c33dec107c2e16e0dd65c7bcc7",
        #   "documentHash": "aeb7e657b46b5cb872ca8e68c373acd40bf0736895003edfa5a6421b5a35faa7",
        #   "versionCreatedAt": 1580832599.0,
        #   "versionNumber": 1,
        #   "entryHash": "ce76344336a331c0eed59d699acedc0a271e77de056295292498ba83e78ec1f2",
        #   "index": "1"
        # },
        # {
        #   "documentHash": "74de57558ebeb1fa0f92d5c6d8f7e10bf36be4c14dc5afa9a323774b4dfda70a",
        #   "versionCreatedAt": 1580901057.0,
        #   "versionNumber": 2,
        #   "entryHash": "af1f4ddcadaa894901ca3a2ae21ad691e8badec991a6bc9bdfd86967a5ddaff0",
        #   "index": "2"
        # },
        # {
        #   "documentHash": "74de57558ebeb1fa0f92d5c6d8f7e10bf36be4c14dc5afa9a323774b4dfda70a",
        #   "versionCreatedAt": 1580901112.0,
        #   "versionNumber": 3,
        #   "entryHash": "ad776d4d212988127c6bffe5be4070ded1a6588c757f5b0be0c40faed4562453",
        #   "index": "3"
        # }

        # versions = []


if __name__ == "__main__":

    pass
    
    #get_project("TestProject")
    #create_project("Test Project", "This is a test project", "West Street, Farnham, Surrey")



