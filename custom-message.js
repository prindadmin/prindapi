console.log('Loading function');

exports.handler = async (event, context) => {
    console.log('Received event:', JSON.stringify(event, null, 2));

    var stage = process.env.ENVIRONMENT_NAME;
    var portalHostname = 'portal'
    
    if (stage === 'dev') {
        portalHostname = 'portal-dev'
    }
    else if (stage === 'staging') {
        portalHostname = 'portal-staging'
    }

    var confirmEmailMessage = `
      Please confirm your sign up by clicking 
      <a href="https://${portalHostname}.prind.tech/#/confirm-email?client_id=${event.callerContext.clientId}&user_name=${event.userName}&confirmation_code=${event.request.codeParameter}">this link</a>
    `;

    var forgotPasswordMessage = `
      Please reset your password by clicking 
      <a href="https://${portalHostname}.prind.tech/#/reset-password?client_id=${event.callerContext.clientId}&user_name=${event.userName}&confirmation_code=${event.request.codeParameter}">this link</a>
    `;

    if (event.triggerSource === "CustomMessage_SignUp") {
      event.response.emailSubject = "Please verify your email address";
      event.response.emailMessage = confirmEmailMessage;
      event.response.smsMessage = "Welcome to the service. Your confirmation code is " + event.request.codeParameter;
    }

    else if (event.triggerSource === "CustomMessage_ForgotPassword") {
        event.response.emailSubject = "Your password reset";
        event.response.emailMessage = forgotPasswordMessage;
        event.response.smsMessage = "Welcome to the service. Your confirmation code is " + event.request.codeParameter;
    }

    console.log('Returned event:', JSON.stringify(event, null, 2));

    return event;
};
