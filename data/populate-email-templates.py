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
    }
]

client = boto3.client('ses',region_name=AWS_REGION)

html_templates_folder = f"{current_directory}/email-templates/html"
text_templates_folder = f"{current_directory}/email-templates/text"

# files = [f for f in listdir(html_templates_folder) if isfile(join(html_templates_folder, f))]

for template in templates:

    # file_name_without_extension = f"{file.split('.html')[-2]}"

    # html_file_name = f"{file_name_without_extension}.html"
    # text_file_name = f"{file_name_without_extension}.txt"

    # template_name = file_name_without_extension.split('email-template-')[0]

    # print(template['template_name'])

    html_file_object = open(join(html_templates_folder, template['html_file_name']))
    text_file_object = open(join(text_templates_folder, template['text_file_name']))

    # print(html_file_object.read())
    
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


