import logging
import os

import tornado.web
import tornado.wsgi
from tornado.web import url

from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

import forms
import models

# Constants
IS_DEV = os.environ['SERVER_SOFTWARE'].startswith('Dev')  # Development server

class Application(tornado.wsgi.WSGIApplication):
  def __init__(self):
    handlers = [
      (r'/', IndexHandler),
      (r'/login', LoginHandler),
    ]
    settings = dict(
      template_path=os.path.join(os.path.dirname(__file__), 'templates'),
      xsrf_cookies=True,
      cookie_secret="asjidoh91239jasdasdasdasdasdkja8izxc21312sjdhsa/Vo=",
      login_url="/login",
    )
    tornado.wsgi.WSGIApplication.__init__(self, handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
  def get_current_user(self):
    user_key = self.get_secure_cookie('user_key')
    if not user_key:
      return None
    return models.User.get(user_key)


class IndexHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
    self.write("welcome %s" % self.current_user)


class LoginHandler(BaseHandler):
  def get(self):
    self.render('login.html', form=forms.LoginForm())

  def post(self):
    form = forms.LoginForm(self)
    if form.validate():
      user = models.User.authenticate(form.email.data, form.password.data)
      if user is None:
        self.render('login.html', form=form)
      else:
        self.set_secure_cookie('user_key', str(user.key()))
        self.redirect(self.get_argument('next', '/'))
    else:
      self.render('login.html', form=form)


def main():
  run_wsgi_app(Application())

if __name__ == '__main__':
  main()