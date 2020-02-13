import boto3
import time
import json
import os

from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key, Attr

from modules import errors


# If logger hasn't been set up by a calling function, set it here

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

class Notification():   

    def __init__(self, username, notification_id):

        # logger.info(log.function_start_output())

        response = table.get_item(
            Key={
                "pk": f"user_{username}",
                "sk": notification_id
            }
        )

        try:
            item = response['Item']
        except KeyError:
            raise errors.NotificationNotFound(f"The notification with ID {notification_id} was not found.")

        self.notification_id = notification_id
        self.notification_unique_part = self.notification_id.split('_')[-1]
        self.username = username
        self.subject = item.get('subject')
        self.message = item.get('message')
        self.is_unread = item.get('status') == 'unread'
        self.is_read = item.get('status') == 'read'
        self.is_archived = item.get('status') == 'archived'

    def change_status(self, state):

        if state not in ['read', 'unread', 'archived']:
            raise Exception(f'Invalid State {state}')

        if state == 'archived':

            table.delete_item(
                Key={
                    "pk": f"user_{self.username}",
                    "sk": self.notification_id
                }
            )

            notification_id = f"notification_{state}_{self.notification_unique_part}"

        table.put_item(
            Item={    
                "pk": f"user_{self.username}",
                "sk": notification_id,
                "subject": self.subject,
                "message": self.message,
                "status": state
            }
        )

        return notification_id

    def archive(self):

        notification_id = self.change_status('archived')

        return notification_id
        

def create_notification(username, subject, message):

    # make an id that will be unique to this user
    notification_unique_part = int(time.time()*10000000)

    notification_id = f"notification_{notification_unique_part}"

    table.put_item(
        Item={    
            "pk": f"user_{username}",
            "sk": notification_id,
            "subject": subject,
            "message": message
        }
    )

    return notification_id


def get_notifications(username, state='unarchived'):

    if state not in ['unarchived', 'archived']:
        raise Exception(f'Invalid State {state}')

    if state == 'archived':
        query_string = "notification_archived"
    else:
        query_string = "notification"

    response = table.query(
         KeyConditionExpression=Key("pk").eq(f"user_{username}") & Key("sk").begins_with(query_string)
    )

    items = response['Items']
    
    notifications = []

    for item in items:

        item['notificationId'] = item.pop('sk')
        item.pop('pk')
        notifications.append(item)

    return notifications



