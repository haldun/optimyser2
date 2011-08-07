import tornado.web

class Form(tornado.web.UIModule):
  def render(self, form):
    return self.render_string('modules/form.html', form=form)


class OriginalPageCode(tornado.web.UIModule):
  def render(self, experiment):
    return self.render_string('modules/original_page_code.js',
                              experiment=experiment).replace('\n', '')

class AlternativePageCode(tornado.web.UIModule):
  def render(self, experiment):
    return self.render_string('modules/alternative_page_code.js',
                              experiment=experiment)


class GoalPageCode(tornado.web.UIModule):
  def render(self, experiment):
    return 'goal page!'
