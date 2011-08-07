import binascii
import logging
import os

import tornado.web
import tornado.wsgi
from tornado.web import url

from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

import forms
import models
import uimodules
import util

# Constants
IS_DEV = os.environ['SERVER_SOFTWARE'].startswith('Dev')  # Development server

class Application(tornado.wsgi.WSGIApplication):
  def __init__(self):
    handlers = [
      (r'/', IndexHandler),
      (r'/signin', SigninHandler),
      (r'/signup', SignupHandler),
      (r'/signout', SignoutHandler),
      (r'/create', CreateExperimentHandler),
      (r'/test', TestExperimentHandler),
      (r'/goal', GoalExperimentHandler),
    ]
    settings = dict(
      debug=True,
      template_path=os.path.join(os.path.dirname(__file__), 'templates'),
      xsrf_cookies=True,
      cookie_secret="asjidoh91239jasdasdasdasdasdkja8izxc21312sjdhsa/Vo=",
      login_url="/signin",
      ui_modules=uimodules,
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
    experiment = models.Experiment.all()[0]
    self.write(dict(a=list(experiment.get_counters())))
    # self.write("welcome %s" % self.current_user)


class SigninHandler(BaseHandler):
  def get(self):
    self.render('signin.html', form=forms.SigninForm())

  def post(self):
    form = forms.SigninForm(self)
    if form.validate():
      user = models.User.authenticate(form.email.data, form.password.data)
      if user is None:
        self.render('signin.html', form=form)
      else:
        self.set_secure_cookie('user_key', str(user.key()))
        self.redirect(self.get_argument('next', '/'))
    else:
      self.render('signin.html', form=form)


class SignupHandler(BaseHandler):
  def get(self):
    self.render('signup.html', form=forms.SignupForm())

  def post(self):
    form = forms.SignupForm(self)
    if form.validate():
      user = models.User(first_name=form.first_name.data,
                         last_name=form.last_name.data,
                         email=form.email.data,
                         password=form.password.data)
      user.put()
      self.set_secure_cookie('user_key', str(user.key()))
      self.redirect(self.get_argument('next', '/'))
    else:
      self.render('signup.html', form=form)


class SignoutHandler(BaseHandler):
  def get(self):
    self.clear_cookie('user_key')
    self.redirect(self.get_argument('next', '/'))


class CreateExperimentHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
    form = forms.ABExperimentForm()
    self.render('create.html', form=form)

  @tornado.web.authenticated
  def post(self):
    form = forms.ABExperimentForm(self)
    if form.validate():
      exp = models.ABExperiment(
          key_name='a' + binascii.hexlify(util._random_bytes(16)),
          user=self.current_user,
          **form.data)
      for alternative in form.alternatives.data:
        exp.alternative_names.append(alternative['name'])
        exp.alternative_urls.append(db.Link(alternative['url']))
      exp.put()
      self.redirect('/')
    else:
      self.render('create.html', form=form)


class TestExperimentHandler(BaseHandler):
  def get(self):
    # TODO Cache
    experiment = models.ABExperiment.get_by_key_name(self.get_argument('e'))
    # TODO Is this experiment running?
    # TODO Is this a preview?
    index = experiment.pick_index()
    self.write('''(function(){
  var createCookie = function(name,value,days) {
    if (days) {
      var date = new Date();
      date.setTime(date.getTime()+(days*24*60*60*1000));
      var expires = "; expires="+date.toGMTString();
    }
    else var expires = "";
    document.cookie = name+"="+value+expires+"; path=/";
  }
  createCookie('opt_selected', %(index)s);
  document.location.href="%(url)s";
})();
''' % dict(index=index, url=experiment.test_links[index]))


class GoalExperimentHandler(BaseHandler):
  pass


def main():
  run_wsgi_app(Application())

if __name__ == '__main__':
  main()