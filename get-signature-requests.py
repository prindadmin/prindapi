import boto3
import os
import time

from modules import errors
from modules import document
from modules import user

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["TABLE_NAME"])

def lambda_handler(event, context):

    try:

        authenticating_user = user.User(event['cognitoPoolClaims']['sub'])
 
        response = table.query(
            KeyConditionExpression=Key("pk").eq(f"user_{authenticating_user.username}") 
                                 & Key("sk").begins_with("documentSignRequest_")
        )

        items = response.get('Items',[])

        #print(items)

        signing_requests = []

        for item in items:
            item.pop('pk')
            item['documentDid'] = item.pop('sk').split('documentSignRequest_')[1]
            requesting_user = user.User(item.pop('requestedBy'))
            item['requestedBy'] = {}
            item['requestedBy']['username'] = requesting_user.username
            item['requestedBy']['firstName'] = requesting_user.first_name
            item['requestedBy']['lastName'] = requesting_user.last_name

            signing_requests.append(item)

        #print(signing_requests)


   # catch any application errors
    except:
        raise

    # except errors.ApplicationError as error:
    #     return {
    #         'statusCode': 400,
    #         "Error": error.get_error_dict()
    #     }
    # # catch unhandled exceptions
    # except Exception as e:
        
    #     # logger.error(log.logging.exception("message"))

    #     return {
    #         'statusCode': 500,
    #         'Error': errors.UnhandledException(context.log_group_name, context.log_stream_name, context.aws_request_id).get_error_dict()
    #     }

    
    return {
        "statusCode": 200,
        "body": signing_requests
    }


if __name__ == '__main__':

    event = {
        "cognitoPoolClaims": {
            #"sub": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa"
            "sub": "778bd486-4684-482b-9565-1c2a51367b8c"
        }
    }

    print(lambda_handler(event, {}))