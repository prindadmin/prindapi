class ApplicationError(Exception):
    
    def __init__(self, message, code, number):
        self.message = message
        self.code = code
        self.number = number

        self.error_dict = {
            "ErrorMessage" : self.message,
            "ErrorCode" : self.code,
            "ErrorNumber" : self.number
        }

        #logger.error('Exception raised: {}'.format(self.error_dict))

    def get_error_dict(self):
   
        return self.error_dict

# this is used for unhandled exceptions in the lambda functions
class UnhandledException(ApplicationError):
    def __init__(self, log_group=None, log_stream=None, request_id=None):
        self.message = "Server error occurred, please contact Technical Support quoting these details: " \
                        "Log group name: {} " \
                        "Log stream name {} " \
                        "Request ID {}" \
                        "".format(log_group, log_stream, request_id)
        
        ApplicationError.__init__(self, self.message, "SERVER_ERROR", "0001")

# CognitoUsername does not have a DID
class DIDNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "DID_NOT_FOUND", "0002")

# Project does not exist in the database
class ProjectNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "PROJECT_NOT_FOUND", "0003")

# Role does not exist in the database
class RoleNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "ROLE_NOT_FOUND", "0004")

# User does not exist in the database
class UserNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "USER_NOT_FOUND", "0005")

# Project ID is not unique
class ProjectAlreadyExists(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "PROJECT_ALREADY_EXISTS", "0006")

class InsufficientPermission(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "INSUFFICIENT_PERMISSION", "0007")

class DocumentNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "DOCUMENT_NOT_FOUND", "0008")

class PageNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "PAGE_NOT_FOUND", "0009")

class DocumentVersionNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "DOCUMENT_VERSION_NOT_FOUND", "0010")

# Role does not exist in the database
class NotifiatinoNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "NOTIFICATION_NOT_FOUND", "0011")

# Email template not found
class TemplateNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "TEMPLATE_NOT_FOUND", "0012")

# Field not found
class FieldNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "FIELD_NOT_FOUND", "0013")

# Field was not the expected type
class InvalidFieldType(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "INVALID_FIELD_TYPE", "0014")

# Invitation not found
class InvitationNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "INVITATION_NOT_FOUND", "0015")

# File not found
class FileNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "FILE_NOT_FOUND", "0016")

# Document Version Exists - when updating a document
class DocumentVersionExists(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "DOCUMENT_VERSION_EXISTS", "0017")

# Foundations API Call Error
class FoundationsApiError(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "FOUNDATIONS_API_ERROR", "0018")

class MissingRequiredFields(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "MISSING_REQUIRED_FIELDS", "0019")

# Signing Request Not Found
class SigningRequestNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "SIGNING_REQUEST_NOT_FOUND", "0020")

class InvalidProjectType(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "INVALID_PROJECT_TYPE", "0021")

class InvalidProcoreAuth(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "INVALID_PROCORE_AUTH", "0022")

class ProcoreApiError(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "PROCORE_API_ERROR", "00023")

class ItemNotFound(ApplicationError):
    def __init__(self, message):
        ApplicationError.__init__(self, message, "ITEM_NOT_FOUND", "0024")



