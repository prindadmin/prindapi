# create a project
myusername="778bd486-4684-482b-9565-1c2a51367b8c"
from modules import project
project.create_project(
    project_name="Project Number Four",
    project_creator=myusername,
    project_description="This is the forth test project",
    site_address="10 High Street, Newtown",
    occupied_during_works=True,
    workplace_when_completed=True)


# list projects
from modules import project
project.list_all_projects()


# create a user
from modules import user
myusername="778bd486-4684-482b-9565-1c2a51367b8c"
user.create_user(username=myusername, name="Bill Smith")

# update a user
from modules import user
myuser = user.User("778bd486-4684-482b-9565-1c2a51367b8c")
myuser.update(email_address="mr.simon.hunt+test1@gmail.com")


# create another user
from modules import user
this_username="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa"
user.create_user(username=this_username, name="Ian Jones")

# get user
from modules import user
myusername="778bd486-4684-482b-9565-1c2a51367b8c"
myuser = user.User(myusername)
print(myuser.name)

# list all users
from modules import user
users = user.list_all_users()
print(users)

# list roles
from modules import role
roles = role.list_all_roles()
print(roles)


# add a project role
myusername="778bd486-4684-482b-9565-1c2a51367b8c"
this_username="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa"
from modules import project
this_project = project.Project('ProjectNumberFour')
this_project.add_user_role(
        requesting_user_name=myusername,
        user_to_add=this_username,
        role_id="projectConsultant"
    )

# invite user to project
myusername="778bd486-4684-482b-9565-1c2a51367b8c"
#this_username="f9c255cb-a42b-4359-a8bd-2ebec5dfa2fa"
invitee_email="mr.simon.hunt+test16@gmail.com"
from modules import project
this_project = project.Project('ProjectNumberFour')
this_project.invite_user(
        requesting_user_name=myusername,
        invitee_email=invitee_email,
        role_id="projectConsultant"
    )

# remove user from project
myusername="778bd486-4684-482b-9565-1c2a51367b8c"
this_username="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa"
from modules import project
this_project = project.Project('ProjectNumberFour')
this_project.remove_user(
        requesting_user_name=myusername,
        user_to_remove=this_username
    )

#respond to invitation
username="f9c255cb-a42b-4359-a8bd-2ebec5dfa2fa"
from modules import project
this_project = project.Project('ProjectNumberFour')
this_project.respond_to_invitation(
        username=username,
        accepted=True
    )


# get project invitations
username="d7b4396c-e7d5-4190-b449-6d4cdf976473"
from modules import user
this_user = user.User(username)
print(this_user.get_project_invitations()) 


# get project roles
from modules import project
this_project = project.Project('ProjectNumberFour')
this_project.get_project_roles()

# update project
from modules import project
this_project = project.Project('ProjectNumberFour')
this_project.update(workplace_when_completed=False)


# get project
from modules import project
this_project = project.Project('ProjectNumberFour')
print(this_project.project_id)
print(this_project.name)
print(this_project.description)
print(this_project.site_address)
print(this_project.occupied_during_works)
print(this_project.workplace_when_completed)

# get page default fields
from modules import page
this_page = page.Page('inception', 'ProjectNumberFour')
print(this_page.default_fields)

# get field (field module)
from modules import field
myfield = field.Field(project_id="ProjectNumberSix", page_name="inception", field_index=1)
myfield.get()

# get page fields
from modules import page
this_page = page.Page('inception', 'ProjectNumberFour')
print(this_page.get_resultant_fields())

# write field
from modules import page
this_page = page.Page('construction', 'ProjectNumberFour')
this_page.write_field(field_index=2, field_type='dropdown', field_data='hello')

# write document field
from modules import page
document_did = 'did:fnds:123451235612346236'
this_page = page.Page('inception', 'ProjectNumberFour')
this_page.write_document_field(field_index=1, document_did=document_did)

# get document version signatures
from modules import document
this_document = document.Document(
    project_id='ProjectNumberFour',
    page='inception',
    field_index=1
)
this_document.get_version_signatures(1)

# get document version
from modules import document
this_document = document.Document(
    project_id='ProjectNumberFour',
    page='inception',
    field_index=1
)
this_document.get_version(0)

# get document current version number
from modules import document
this_document = document.Document(
    project_id='ProjectNumberFour',
    page='inception',
    field_index=1
)
this_document.get_current_version_number()

# get all document info
from modules import document
this_document = document.Document(
    project_id='ProjectNumberFour',
    page='inception',
    field_index=1
)
this_document.get_all_info()

# create a notification
username = "778bd486-4684-482b-9565-1c2a51367b8c"
from modules import notification
notification.create_notification(username, "test subject 2", "test message 2")

# initialise notification object
username = "778bd486-4684-482b-9565-1c2a51367b8c"
from modules import notification
this_notification = notification.Notification(username, "notification_unread_15814182191147676")

# archive notification
username = "778bd486-4684-482b-9565-1c2a51367b8c"
from modules import notification
this_notification = notification.Notification(username, "notification_15814298872689934")
this_notification.archive()


# get notifications
username = "778bd486-4684-482b-9565-1c2a51367b8c"
from modules import notification
notification.get_notifications(username, state='archived')

# get users projects
username = "778bd486-4684-482b-9565-1c2a51367b8c"
#username = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaa"
from modules import user
this_user = user.User(username)
this_user.get_projects()

# send email
from modules import mail
mail.send_email(
    username="778bd486-4684-482b-9565-1c2a51367b8c",
    template_name="project-invitation",
    template_data={"projectName": "project1", "roleName": "role1", "username": "Simon"}
)


# find parameters in template
from modules import mail
#mail.find_parameters('agagas{{hello}}agadgadga{{you}}agagagd')
mail.find_parameters('agagasagagagd')


# send post-confirmation email
from modules import mail
template_data = {
    "firstName": "Simon",
    "foundationsId": "did:fnds:123456789"
}
mail.send_email("d7b4396c-e7d5-4190-b449-6d4cdf976473", "post-confirmation", template_data)

# get foundations DID
username = "b966f0b7-4310-4608-b08d-418210e7ff20"
from modules import user
this_user = user.User(username)
did = this_user.get_did_from_foundations()
print(did)

# add foundations subscription
username = "b966f0b7-4310-4608-b08d-418210e7ff20"
from modules import user
this_user = user.User(username)
this_user.add_foundations_subscription()

# get foundations subscription
username = "b966f0b7-4310-4608-b08d-418210e7ff20"
from modules import user
this_user = user.User(username)
this_user.get_foundations_subscription()

# get uploaded documents
username = "778bd486-4684-482b-9565-1c2a51367b8c"
from modules import user
this_user = user.User(username)
document_versions = this_user.get_uploaded_document_versions()
print(document_versions)

# get field document DID
from modules import field
this_field = field.Field("1", 'inception', 'ProjectNumberSix')
print(this_field.get_document_did())

# get document field
from modules import document
document.get_document_field("did:fnds:7ce027a56933c1cee47c6d6199063047721db8b6088c6837571c0f7de00a7501")

# get signed documents
from modules import user
username="ab0ae262-eedf-41c0-ac6e-e5109217b6c1"
this_user = user.User(username)
this_user.get_signed_documents()

from modules import project
username="ab0ae262-eedf-41c0-ac6e-e5109217b6c1"
this_project = project.Project("TestingProjectCreatorRole2020-03-03")
this_project.user_in_roles(username, ["creator"])
