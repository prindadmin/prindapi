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

