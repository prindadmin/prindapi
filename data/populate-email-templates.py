"""
Put the text version of the template in email-templates/text
and the html version of the template in email-templates/html
then populate the templates object below with the template name, 
file names and subject

update of create the templates usin the functions below.
"""

import boto3
from botocore.exceptions import ClientError

from os.path import join, dirname, realpath
current_directory = dirname(realpath(__file__))

AWS_REGION = "eu-west-1"

templates = [
    {
        "template_name": "test-template",
        "text_file_name": "email-template-test.txt",
        "html_file_name": "email-template-test.html",
        "subject": "Test email template"
    },
    {
        "template_name": "project-invitation",
        "text_file_name": "email-template-project-invitation.txt",
        "html_file_name": "email-template-project-invitation.html",
        "subject": "You have been invited to join project {{projectName}}"
    },
    {
        "template_name": "project-invitation-response",
        "text_file_name": "email-template-project-invitation-response.txt",
        "html_file_name": "email-template-project-invitation-response.html",
        "subject": "Invitation response for {{inviteeFirstName}} {{inviteeLastName}} on {{projectName}}"
    },
    {
        "template_name": "post-confirmation",
        "text_file_name": "email-template-post-confirmation.txt",
        "html_file_name": "email-template-post-confirmation.html",
        "subject": "Thanks for confirming your email address"
    },
    {
        "template_name": "post-confirmation-forgot-password",
        "text_file_name": "email-template-post-confirmation-forgot-password.txt",
        "html_file_name": "email-template-post-confirmation-forgot-password.html",
        "subject": "Your password has been changed"
    },
    {
        "template_name": "document-signature-request",
        "text_file_name": "email-template-document-signature-request.txt",
        "html_file_name": "email-template-document-signature-request.html",
        "subject": "You have received a request to sign a document"
    }
]

client = boto3.client('ses',region_name=AWS_REGION)

html_templates_folder = f"{current_directory}/email-templates/html"
text_templates_folder = f"{current_directory}/email-templates/text"

# files = [f for f in listdir(html_templates_folder) if isfile(join(html_templates_folder, f))]

def create_all_templates():

    template_names = [template['template_name'] for template in templates]

    create_templates(template_names)

def create_templates(template_names):

    for template in templates:

        if template['template_name'] in template_names:

            html_file_object = open(join(html_templates_folder, template['html_file_name']))
            text_file_object = open(join(text_templates_folder, template['text_file_name']))
            
            try:
                response = client.create_template(
                    Template={
                        'TemplateName': template['template_name'],
                        'SubjectPart': template['subject'],
                        'TextPart': text_file_object.read(),
                        'HtmlPart': html_file_object.read()
                    }
                )
            except ClientError as e:
                print(e.response['Error']['Message'])
            else:
                print("Template created")

            html_file_object.close()
            text_file_object.close()

def update_templates(template_names):

    for template in templates:

        if template['template_name'] in template_names:

            html_file_object = open(join(html_templates_folder, template['html_file_name']))
            text_file_object = open(join(text_templates_folder, template['text_file_name']))

            try:
                response = client.update_template(
                    Template={
                        'TemplateName': template['template_name'],
                        'SubjectPart': template['subject'],
                        'TextPart': text_file_object.read(),
                        'HtmlPart': html_file_object.read()
                    }
                )
            except ClientError as e:
                print(e.response['Error']['Message'])
            else:
                print("Template created")

            html_file_object.close()
            text_file_object.close()

if __name__ == '__main__':

    update_templates(['project-invitation', 'document-signature-request'])
    #create_templates(['post-confirmation-forgot-password'])
    #create_all_templates()
    #update_templates(['test-template'])