import random

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.ext.db import polymodel

import bcrypt
import counter

class User(db.Model):
  email = db.EmailProperty()
  first_name = db.StringProperty()
  last_name = db.StringProperty()
  password_hash = db.StringProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)
  last_logged_in = db.DateTimeProperty()

  def __init__(self, *args, **kwds):
    db.Model.__init__(self, *args, **kwds)
    password = kwds.pop('password', None)
    if password:
      self.set_password(password)


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


class Experiment(polymodel.PolyModel):
  user = db.ReferenceProperty(User, collection_name='ab_experiments')
  name = db.StringProperty(required=True)


class ABExperiment(Experiment):
  original = db.LinkProperty(required=True)
  alternative_urls = db.ListProperty(db.Link)
  alternative_names = db.ListProperty(unicode)
  goal = db.LinkProperty(required=False)
  is_active = db.BooleanProperty(default=False)
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

  _test_links = None

  @property
  def test_links(self):
    if self._test_links is None:
      self._test_links = [self.original]
      self._test_links.extend(self.alternative_urls)
    return self._test_links

  def pick_index(self):
    return random.choice(range(len(self.test_links)))

  @property
  def alternatives(self):
    return zip(self.alternative_names, self.alternative_urls)

  _counters = None

  def get_counters(self):
    if self._counters is None:
      self._counters = [
      (counter.get_count('%s:%s:visit' % (self.key().name(), i)),
      counter.get_count('%s:%s:conversion' % (self.key().name(), i)))
      for i, _ in enumerate(self.test_links)
      ]
    return self._counters
