import boto3
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])


from modules import log
from modules.log import logger

try:
    stage_log_level = os.environ['PRIND_LOG_LEVEL']
except (NameError, KeyError):
    stage_log_level = 'CRITICAL'

print('stage_log_level:', stage_log_level)

# set the log level
log.set_logging_level(stage_log_level)

from modules import user
from modules import did as didmod

def lambda_handler(event, context):

    for record in event["Records"]:

        message = json.loads(record["Sns"]["Message"])
       
        # a user has signed up with a previously queried email address
        if message["notificationType"] == "signUp":

            # first get the username for the email address
            response = table.query(
                IndexName="GSI1",
                KeyConditionExpression=Key("sk").eq("userDetails_emailAddress")&Key("data").eq(message["emailAddress"])
            )

            username = response['Items'][0].get('pk').split("user_")[1]

            did = message["foundationsId"]

            print(f"Adding FoundationsId {foundationsId} for username {username}")

            this_user = user.User(username)
            this_user.write_did(did)

            this_user.add_foundations_subscription()

        elif message["notificationType"] == "fieldRequestApproved":
            
            print("fieldRequestApproved notification received")
            print(message)

        elif message["notificationType"] == "fieldRequestDenied":

            print("fieldRequestDenied notification received")
            print(message)

        elif message["notificationType"] == "documentSigned":

            print(message['signingDid'])
            did_obj = didmod.Did(message['signingDid'])
            username = did_obj.get_cognito_username()

            this_user = user.User(username)
            this_user.add_signed_document(
                document_did=message['documentDid'], 
                document_version=message['documentVersion'], 
                signed_at=message['signedAt'], 
                entry_hash=message['entryHash']
            )

if __name__ == '__main__':

    user_signup_notification = {
        "notificationType": "signUp",
        "emailAddress": "mr.simon.hunt+test14@gmail.com",
        "foundationsId": "did:fnds:161263516316213616236"
    }

    field_request_approved_notification = {
        "notificationType" : "fieldRequestApproved",
        "did" : "did:fnds:161263516316213616236",
        "field" : "dateOfBirth",
        "requesterReference" : "Prin-D",
        "userComments" : "Here are the fields you requested"
    }

    field_request_denied_notification = {
        "notificationType" : "fieldRequestDenied",
        "did" : "did:fnds:161263516316213616236",
        "field" : "dateOfBirth",
        "requesterReference" : "Prin-D",
        "userComments" : "You shouldn't need this field"
    }

    document_signed_notification = {
        'notificationType': 'documentSigned', 
        'documentDid': 'did:fnds:b8349b4faeaa271333989c6c0e40f945d1d573d742eb0b5b909d0e330bc85bd7',
        'documentVersion': 2,
        'signingDid': 'did:fnds:31a24b270fe86d9c595e715854028c319cc75957718861eb66996929eb5c8025',
        'signedAt': 1583326444,
        'entryHash': '2129561f791410dca34c6ec2f4b89c8b55e4c9ff31176d0f267b277d7d1b8a63'
    }

    event = {
      "Records": [
        {
          "EventSource": "aws:sns",
          "EventVersion": "1.0",
          "EventSubscriptionArn": "arn:aws:sns:eu-west-1:514296467270:d85be1f5baa83fa83850d8b58731a7f7c8ba65c33dec107c2e16e0dd65c7bcc7:e1cedc2b-9bfe-41ff-a874-6304ad7da720",
          "Sns": {
            "Type": "Notification",
            "MessageId": "ecab1301-9135-5c53-bf7b-45c4540ad715",
            "TopicArn": "arn:aws:sns:eu-west-1:514296467270:d85be1f5baa83fa83850d8b58731a7f7c8ba65c33dec107c2e16e0dd65c7bcc7",
            "Subject": None,
            "Message": json.dumps(document_signed_notification),
            "Timestamp": "2020-02-18T10:57:03.487Z",
            "SignatureVersion": "1",
            "Signature": "ayqaWSNdyBVO5hl3sQ/PIT3IUSCAPBCrMIdSPoDMxLmF2EVgFGz3xGkHBEKyJbeutr40b5+IXrIJKlq1X0mZ4Nsn9shtcJMNnlVxGV6584n4s6WiJq5kkuDyHcFVpOTuuMfF34W2XGx7dcNcrcMYZb89IrS8VRk00cp4RXfiWTEZyaKn21+Akw7LTUP55JmlJzkVWtugHZmZKt19haEA9CInsWDga8G/hldx2ZkSTJzPjyUUqwxt+2eJHAugZjyP6Lenv2ri638+21mEOVvdiNWUlqes7olPDowRNoFI+e8DULET5L2PUfKxlr91Vr4/ldef46SRUnqBI19XMhCrbw==",
            "SigningCertUrl": "https://sns.eu-west-1.amazonaws.com/SimpleNotificationService-a86cb10b4e1f29c941702d737128f7b6.pem",
            "UnsubscribeUrl": "https://sns.eu-west-1.amazonaws.com/?Action=Unsubscribe&SubscriptionArn=arn:aws:sns:eu-west-1:514296467270:d85be1f5baa83fa83850d8b58731a7f7c8ba65c33dec107c2e16e0dd65c7bcc7:e1cedc2b-9bfe-41ff-a874-6304ad7da720",
            "MessageAttributes": {}
          }
        }
      ]
    }

    lambda_handler(event, {})
        
