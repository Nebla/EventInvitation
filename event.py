import os

from google.appengine.ext import ndb

import jinja2
import webapp2

import json

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_EVENT_NAME = 'event_group'

def event_key(event_name=DEFAULT_EVENT_NAME):
    # Constructs a Datastore key for a Event entity.
    return ndb.Key('Events', event_name)

class Event(ndb.Model):
    identity = ndb.StringProperty(indexed=True)
    name = ndb.StringProperty(indexed=False)
    available = ndb.IntegerProperty(indexed=False)
    total = ndb.IntegerProperty(indexed=False)
    creationDate = ndb.DateTimeProperty(auto_now_add=True)

class User(ndb.Model):
    email = ndb.StringProperty(indexed=True)
    name = ndb.StringProperty(indexed=False)
    company = ndb.StringProperty(indexed=False)

class EventPage(webapp2.RequestHandler):
    def get(self):
        event_id = self.request.get('eventId')
        event_query = Event.query(Event.identity == event_id, ancestor=event_key())
        event = event_query.get()
        if (event):
            template_values = {
                'event': event,
            }
            template = JINJA_ENVIRONMENT.get_template('event.html')
            self.response.write(template.render(template_values))
        else:
            self.response.status_int = 404
            self.response.status = "404 - Not found"
            self.response.body = "The event can not be found. Check your url (eventId) or contact your system administrator."

    def post(self):
        event_id = self.request.get('eventId')
        event_query = Event.query(Event.identity == event_id, ancestor=event_key())
        event = event_query.get()

        if (event):
            if event.available > 0:
                eventKey = ndb.Key("Events", event_key().id(), "Event", event.key.id())
                user = User(parent=eventKey)
                jsonobject = json.loads(self.request.body)
                user.email = jsonobject.get('userEmail')
                user.name = jsonobject.get('userName')
                user.company = jsonobject.get('userCompany')
                user.put()
                event.available -= 1
                event.put()
                self.response.out.write(json.dumps({'status': 'success'}))
            else:
                self.response.out.write(json.dumps({'status': 'event full'}))
        else:
            self.response.status_int = 404
            self.response.status = "404 - Not found"
            self.response.body = "The event can not be found. Check your url (eventId) or contact your system administrator."

    def delete(self):
        event_id = self.request.get('eventId')
        event_query = Event.query(Event.identity == event_id, ancestor=event_key())
        event = event_query.get()
        eventKey = ndb.Key("Events", event_key().id(), "Event", event.key.id())
        eventKey.delete()

class EventStatus(webapp2.RequestHandler):
    def get(self):
        event_id = self.request.get('eventId')
        event_query = Event.query(Event.identity == event_id, ancestor=event_key())
        event = event_query.get()
        eventKey = ndb.Key("Events", event_key().id(), "Event", event.key.id())
        user_query = User.query(ancestor=eventKey)
        users = user_query.fetch()

        if (event):
            template_values = {
                'event': event,
                'users': users
            }
            template = JINJA_ENVIRONMENT.get_template('status.html')
            self.response.write(template.render(template_values))
        else:
            self.response.status_int = 404
            self.response.status = "404 - Not found"
            self.response.body = "The event can not be found. Check your url (eventId) or contact your system administrator."

class UserStatus(webapp2.RequestHandler):
    def get(self):
        event_id = self.request.get('eventId')
        user_email = self.request.get('userId')
        event_query = Event.query(Event.identity == event_id, ancestor=event_key())
        event = event_query.get()

        if event:
            eventKey = ndb.Key("Events", event_key().id(), "Event", event.key.id())
            user_query = User.query(User.email == user_email, ancestor=eventKey)
            user = user_query.get()
            self.response.headers['Content-Type'] = "application/json"
            if user:
                self.response.out.write(json.dumps({'confirmed': 'true'}))
            else:
                self.response.out.write(json.dumps({'confirmed': 'false'}))
        else:
            self.response.status_int = 404
            self.response.status = "404 - Not found"
            self.response.body = "The event can not be found. Check your url (eventId) or contact your system administrator."

class Admin(webapp2.RequestHandler):
    def get(self):
        events_query = Event.query(ancestor=event_key()).order(-Event.creationDate)
        events = events_query.fetch()
        template_values = {
            'events': events,
        }
        template = JINJA_ENVIRONMENT.get_template('create.html')
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

        self.redirect('/create')

app = webapp2.WSGIApplication([
                                  ('/event', EventPage),
                                  ('/userStatus', UserStatus),
                                  ('/eventStatus', EventStatus),
                                  ('/create', Admin),
                                  ('/', Admin),
                              ], debug=True)
