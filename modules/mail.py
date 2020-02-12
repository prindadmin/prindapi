import boto3
import json
from botocore.exceptions import ClientError

SENDER = "mail@prind.tech"
AWS_REGION = "eu-west-1"
CHARSET = "UTF-8"

# Create a new SES resource and specify a region.
client = boto3.client('ses',region_name=AWS_REGION)


def send_project_invitation_email(username, project_id, project_name, role_id, role_name):

    #
    # Get the email address from the username in future, for now I'm hard coding it

    RECIPIENT = 'simon.hunt@prind.tech'
    template_data = {
        "projectId": project_id,
        "projectName": project_name,
        "roleId": role_id,
        "roleName": role_name
    }

    try:
        #Provide the contents of the email.
        response = client.send_templated_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Source=SENDER,
            Template="project-invitation",
            TemplateData=json.dumps(template_data)
        )
    # Display an error if something goes wrong. 
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


if __name__ == '__main__':

    send_project_invitation_email('a cognito user', 'TestProject1', 'The First Project', 'client', 'The Client')

