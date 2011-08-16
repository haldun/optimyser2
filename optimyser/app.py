import binascii
import logging
import os

import tornado.web
import tornado.wsgi
from tornado.web import url

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app

import counter
import forms
import models
import uimodules
import util

# Constants
IS_DEV = os.environ['SERVER_SOFTWARE'].startswith('Dev')  # Development server

class Application(tornado.wsgi.WSGIApplication):
  def __init__(self):
    handlers = [
      url(r'/', IndexHandler),
      url(r'/signin', SigninHandler),
      url(r'/signup', SignupHandler),
      url(r'/signout', SignoutHandler),
      url(r'/home', HomeHandler, name='home'),
      url(r'/report/([^/]+)', ReportHandler, name='report'),
      url(r'/create', CreateExperimentHandler),
      url(r'/install/([^/]+)', InstallExperimentHandler, name='install'),
      url(r'/preview/([^/]+)', PreviewExperimentHandler, name='preview'),
      url(r'/options.js', OptionsHandler, name='options'),
      url(r'/v', VisitHandler, name='visit'),
      url(r'/c', ConversionHandler, name='conversion'),
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
  def get(self):
    self.write("optimyser")


# Authentication handlers

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


# Dashboard handlers

class HomeHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self):
    experiments = models.Experiment.all().filter('user =', self.current_user)
    self.render('home.html', experiments=experiments)


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
      self.redirect(self.reverse_url('install', exp.key().name()))
    else:
      self.render('create.html', form=form)


class InstallExperimentHandler(BaseHandler):
  @tornado.web.authenticated
  def get(self, key_name):
    experiment = models.ABExperiment.get_by_key_name(key_name)
    if experiment.user.key() != self.current_user.key():
      raise tornado.web.HTTPError(403)
    self.render('install.html', experiment=experiment)


class ReportHandler(BaseHandler):
  # TODO Implement me
  @tornado.web.authenticated
  def get(self, key_name):
    experiment = models.ABExperiment.get_by_key_name(key_name)
    if experiment.user.key() != self.current_user.key():
      raise tornado.web.HTTPError(403)
    self.write(dict(r=experiment.get_counters()))
    report_cache_key = '%s:reports' % experiment.key().name()
    reports = memcache.get(report_cache_key)
    if reports is None:
      reports = experiment.get_counters()
      if not memcache.add(report_cache_key, reports):
        logging.error("Cannot set memcache key")
    self.render('report.html', experiment=experiment, reports=reports)
    # self.render('report.html', experiment=experiment)


class PreviewExperimentHandler(BaseHandler):
  # TODO Implement me
  @tornado.web.authenticated
  def get(self, key_name):
    experiment = models.ABExperiment.get_by_key_name(key_name)
    if experiment.user.key() != self.current_user.key():
      raise tornado.web.HTTPError(403)


# Counter handlers

class JSHandler(BaseHandler):
  def prepare(self):
    key_name = self.get_argument('e')
    cache_key = 'experiment:%s' % key_name
    experiment = memcache.get(cache_key)
    if experiment is None:
      experiment = models.ABExperiment.get_by_key_name(key_name)
      if not memcache.set(cache_key, experiment):
        logging.error("Cannot set experiment into the memcache")
    if experiment is None:
      raise tornado.web.HTTPError(404)
    if not experiment.is_running:
      # TODO Handle preview case here
      raise tornado.web.HTTPError(404)
    self.experiment = experiment
    self.set_header('Content-Type', 'text/javascript')

  def get_selected(self):
    selected = self.get_argument('s', None)
    if selected is not None:
      try:
        selected = int(selected)
      except:
        selected = -1
    if not (0 <= selected < len(self.experiment.test_links)):
      return None
    return selected


class OptionsHandler(JSHandler):
  def get(self):
    selected = self.get_selected()
    if selected is None:
      selected = self.experiment.pick_index()
    next = self.experiment.test_links[selected]
    self.render('options.js', next=next, index=selected,
                experiment=self.experiment)


class VisitHandler(JSHandler):
  def get(self):
    selected = self.get_selected()
    if selected is None:
      return
    counter.increment('%s:%s:visit' % (self.experiment.key().name(), selected))
    self.write('1')


class ConversionHandler(JSHandler):
  def get(self):
    selected = self.get_selected()
    if selected is None:
      return
    counter.increment('%s:%s:conversion' % (self.experiment.key().name(), selected))
    self.write('1')


def main():
  run_wsgi_app(Application())

if __name__ == '__main__':
  main()