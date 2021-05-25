import os
import json
import boto3

def lambda_handler(event, context):
    
    print(json.dumps(event))

    # Extract the important information
    client_id = event["callerContext"]["clientId"]
    username = event['userName']
    link_parameter = event['request']['linkParameter']
    code_parameter = event['request']['codeParameter']

    # Get the replacement values for the email content
    given_name = ""
    try:
        given_name = event['request']['userAttributes']['given_name']
    except:
        print("given_name not provided")

    # Identify why was this function invoked
    if event["triggerSource"] == "CustomMessage_SignUp":
        
        print("It was a sign up request")
        
        # Identify if this request came from the web portal
        if client_id == os.environ['PRIND_USER_POOL_BROWSER_CLIENT_ID']:

            # Get the URL for the verification code
            verification_code = f"{os.environ['PRIND_PORTAL_CONFIRM_EMAIL_URL']}?client_id={client_id}&user_name={username}&confirmation_code={code_parameter}"

            # If the fetch fails, send as is to ensure something is sent
            try:
                email_template_content = get_email_template("PrinDEmailVerificationLinkDesktop")
            except:
                event["response"]["emailMessage"] = f"Please click the following link to confirm you email address:\r\n\n{verification_code}"
                return event
            
            event["response"]["emailSubject"] = email_template_content['Template']['SubjectPart']
            event["response"]["emailMessage"] = email_template_content['Template']['HtmlPart'].replace('{{firstName}}', given_name).replace('{{verificationLink}}', verification_code)
            return event


        # Identify if this request came from the procore embedded app
        if client_id == os.environ['PRIND_USER_POOL_PROCORE_BROWSER_CLIENT_ID']:

            # Get the URL for the verification code
            verification_code = f"{os.environ['PRIND_PROCORE_CONFIRM_EMAIL_URL']}?client_id={client_id}&user_name={username}&confirmation_code={code_parameter}"

            # If the fetch fails, send as is to ensure something is sent
            try:
                email_template_content = get_email_template("PrinDEmailVerificationLinkDesktop")
            except:
                event["response"]["emailMessage"] = f"Please click the following link to confirm you email address:\r\n\n{verification_code}"
                return event
            
            event["response"]["emailSubject"] = email_template_content['Template']['SubjectPart']
            event["response"]["emailMessage"] = email_template_content['Template']['HtmlPart'].replace('{{firstName}}', given_name).replace('{{verificationLink}}', verification_code)
            return event

    # Custom message for other events
    if event["triggerSource"] == "CustomMessage_ForgotPassword":

        print("It was a forgot password request")

        # Identify if this request came from the web portal
        if client_id == os.environ['PRIND_USER_POOL_BROWSER_CLIENT_ID']:

            # Get the URL for the verification code
            verification_code = f"{os.environ['PRIND_WEBSITE_RESET_PASSWORD_URL']}?user_name={username}&confirmation_code={code_parameter}"

            # If the fetch fails, send as is to ensure something is sent
            try:
                email_template_content = get_email_template("PrinDResetPasswordRequest")
            except:
                event["response"]["emailMessage"] = f"Please click the following link to confirm you email address:\r\n\n{verification_code}"
                return event
            
            event["response"]["emailSubject"] = email_template_content['Template']['SubjectPart']
            event["response"]["emailMessage"] = email_template_content['Template']['HtmlPart'].replace('{{firstName}}', given_name).replace('{{verificationLink}}', verification_code)
            return event


        # Identify if this request came from the procore embedded app
        if client_id == os.environ['PRIND_USER_POOL_PROCORE_BROWSER_CLIENT_ID']:

             # Get the URL for the verification code
            verification_code = f"{os.environ['PRIND_PROCORE_RESET_PASSWORD_URL']}?user_name={username}&confirmation_code={code_parameter}"

            # If the fetch fails, send as is to ensure something is sent
            try:
                email_template_content = get_email_template("PrinDResetPasswordRequest")
            except:
                event["response"]["emailMessage"] = f"Please click the following link to confirm you email address:\r\n\n{verification_code}"
                return event
            
            event["response"]["emailSubject"] = email_template_content['Template']['SubjectPart']
            event["response"]["emailMessage"] = email_template_content['Template']['HtmlPart'].replace('{{firstName}}', given_name).replace('{{verificationLink}}', verification_code)
            return event

    # If the event matches nothing, return original event
    return event


def get_email_template(template_name):
    
    # Create SES client
    ses = boto3.client('ses')
    
    response = ses.get_template(
      TemplateName = template_name
    )
    
    return response