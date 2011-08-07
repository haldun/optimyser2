import tornado.web

class Form(tornado.web.UIModule):
  def render(self, form):
    return self.render_string('modules/form.html', form=form)

