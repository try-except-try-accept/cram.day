from flask_login import LoginManager, UserMixin

class User(UserMixin):
    def __init__(self, id, username, password):
         self.user_id = str(id)
         self.username = username
         self.password = password
         self.authenticated = False
         self.is_admin = username == "mrhallbkk"

    def is_active(self):
         return self.is_active()
    def is_anonymous(self):
         return False
    def is_authenticated(self):
         return self.authenticated
    def is_active(self):
         return True
    def get_id(self):
         return self.user_id
