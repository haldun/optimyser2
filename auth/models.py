from google.appengine.ext import db

import bcrypt

class User(db.Model):
  email = db.EmailProperty()
  first_name = db.StringProperty()
  last_name = db.StringProperty()
  password_hash = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

  def set_password(self, password):
    self.password_hash = bcrypt.hashpw(password, bcrypt.gensalt(log_rounds=1))

  def check_password(self, password):
    return bcrypt.hashpw(password, self.password_hash) == self.password_hash

  @classmethod
  def authenticate(cls, email, password):
    user = cls.all().filter('email =', email).get()
    if user is None:
      return None
    if user.check_password(password):
      return user
    return None
