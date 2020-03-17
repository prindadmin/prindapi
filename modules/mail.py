import boto3
import json
from botocore.exceptions import ClientError
from modules import errors
from modules import user
from modules import log

SENDER = "Prin-D communication <mail@prind.tech>"
AWS_REGION = "eu-west-1"
CHARSET = "UTF-8"

# Create a new SES resource and specify a region.
client = boto3.client('ses',region_name=AWS_REGION)

try:
    logger
except:
    from modules.log import logger
    log.set_logging_level()

def list_template_parameters(template_contents):
    """
    Gets any parameters in the given template in the
    format {{parameter}}
    """

    parameters = []
    s = template_contents
    start = 0

    while start > -1:
        start = s.find("{{")
        end = s.find("}}")

        if start > -1 and end > -1:
                parameters.append(s[start+2:end])

        s = s[end+2::]

    logger.debug(log.function_end_output(locals()))   

    return parameters


def send_email(email_address, template_name, template_data):

    try:
        response = client.get_template(
            TemplateName=template_name
        )
    except ClientError as e:
        raise errors.TemplateNotFound(e.response['Error']['Message'])

    text_template = response['Template'].get('TextPart')
    html_template = response['Template'].get('HtmlPart')
    subject = response['Template'].get('SubjectPart')

    parameters_in_template = set() 

    parameters_in_template = parameters_in_template.union(list_template_parameters(text_template))
    parameters_in_template = parameters_in_template.union(list_template_parameters(html_template))
    parameters_in_template = parameters_in_template.union(list_template_parameters(subject))

    parameters_provided = set(template_data)

    # if not parameters_in_template.issubset(parameters_provided):
    #     missing_parameters = parameters_in_template.difference(parameters_provided)
    #     raise Exception(f'Required parameters not provided: {", ".join(list(missing_parameters))}')

    #
    # Get the email address from the username in future, for now I'm hard coding it

    logger.debug(email_address)

    try:
        #Provide the contents of the email.
        response = client.send_templated_email(
            Destination={
                'ToAddresses': [
                    email_address,
                ],
            },
            Source=SENDER,
            Template=template_name,
            TemplateData=json.dumps(template_data)
        )
    # Display an error if something goes wrong. 
    except ClientError as e:
        logger.debug(e.response['Error']['Message'])
    else:
        logger.debug(response)
        logger.debug("Email sent! Message ID:"),
        logger.debug(response['MessageId'])

    logger.debug(log.function_end_output(locals()))  


if __name__ == '__main__':

    #find_parameters('agagas{{hello}}agadgadga')
    #send_project_invitation_email('a cognito user', 'TestProject1', 'The First Project', 'client', 'The Client')

    pass


