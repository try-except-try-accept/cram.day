# Your User Class
# The class that you use to represent users needs to implement these properties and methods:
#
# is_authenticated
# This property should return True if the user is authenticated, i.e. they have provided valid credentials. (Only authenticated users will fulfill the criteria of login_required.)
#
# is_active
# This property should return True if this is an active user - in addition to being authenticated, they also have activated their account, not been suspended, or any condition your application has for rejecting an account. Inactive accounts may not log in (without being forced of course).
#
# is_anonymous
# This property should return True if this is an anonymous user. (Actual users should return False instead.)
#
# get_id()
# This method must return a str that uniquely identifies this user, and can be used to load the user from the user_loader callback. Note that this must be a str - if the ID is natively an int or some other type, you will need to convert it to str.
#
# To make implementing a user class easier, you can inherit from UserMixin, which provides default implementations for all of these properties and methods. (It’s not required, though.)

from database import authenticate_user

class User:

    def __init__(self, username=None, password=None):


        self.is_authenticated = False
        self.is_active = False
        self.is_anonymous = False

        user_creds = authenticate_user(username, password)

        if user_creds:
            self.is_authenticated = True
            self.is_active = True
            self.username = username
            self.display_name = user_creds['display_name']
            self.user_id = user_creds['user_id']

    def get_id(self):
        return self.user_id

