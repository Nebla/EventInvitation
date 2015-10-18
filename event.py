import os
import urllib

from google.appengine.ext import ndb

import jinja2
import webapp2

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_EVENT_NAME = 'event_group'

def event_key(event_name=DEFAULT_EVENT_NAME):
    # Constructs a Datastore key for a Event entity.
    return ndb.Key('Events', event_name)

class Event(ndb.Model):
    identity = ndb.StringProperty(indexed=False)
    name = ndb.StringProperty(indexed=False)
    available = ndb.IntegerProperty(indexed=False)
    total = ndb.IntegerProperty(indexed=False)
    creationDate = ndb.DateTimeProperty(auto_now_add=True)

class User(ndb.Model):
    identity = ndb.StringProperty(indexed=False)
    admin = ndb.BooleanProperty(indexed=False)
    event = ndb.StructuredProperty(Event)

class Admin(webapp2.RequestHandler):

    def get(self):
        events_query = Event.query(ancestor=event_key()).order(-Event.creationDate)
        events = events_query.fetch()
        template_values = {
            'events': events,
        }
        template = JINJA_ENVIRONMENT.get_template('admin.html')
        self.response.write(template.render(template_values))

    def post(self):
        eventId = self.request.get('eventId')
        eventName = self.request.get('eventName')
        total = self.request.get('total')

        event = Event(parent=event_key())
        event.identity = eventId
        event.name = eventName
        event.available = int(total)
        event.total = int(total)
        event.put()

        query_params = {'event_id': eventId}
        self.redirect('/?' + urllib.urlencode(query_params))


app = webapp2.WSGIApplication([
    #('/', MainPage),
    ('/admin', Admin),
    ('/create', Admin),
], debug=True)
