import boto3
import json
import os

def lambda_handler(event, context):

    for record in event["Records"]:

        message = record["Sns"]["Message"]
        print(message)


        # events

        # - document signed
        # - user with email address xxxx@example.com has joined foundations with did of xxxx
        # - subscription request has been accepted

 
       
if __name__ == '__main__':

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
            "Message": "{\"testName\": \"agklaslgkjasldgj\"}",
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
        
