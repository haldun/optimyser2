from wtforms import *
from wtforms.validators import *

from django.utils.datastructures import MultiValueDict

class BaseForm(Form):
  def __init__(self, handler=None, obj=None, prefix='', formdata=None, **kwargs):
    if handler:
      formdata = MultiValueDict()
      for name in handler.request.arguments.keys():
        formdata.setlist(name, handler.get_arguments(name))
    Form.__init__(self, formdata, obj=obj, prefix=prefix, **kwargs)


class SigninForm(BaseForm):
  email = TextField('email')
  password = PasswordField('password')


class SignupForm(BaseForm):
  first_name = TextField('first name')
  last_name = TextField('first name')
  email = TextField('email')
  password = PasswordField(
      'password',
      [Required(), EqualTo('password_confirmation', message='Passwords must match')])
  password_confirmation = PasswordField('password confirmation')
