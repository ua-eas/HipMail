from google.appengine.ext import webapp 
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler 
from google.appengine.ext.webapp import util
from django.utils import simplejson as json
import logging
import urllib, urllib2
import models
import re
import settings

def sendNotification(sender, message, roomID):
    url = 'http://api.hipchat.com/v1/rooms/message?auth_token=%s&notify=1&format=json' % settings.authToken
    # concatenates the subject of the email with a link to a page showing the message contents.
    data = urllib.urlencode({'room_id': roomID, 
                             'from': 'HipMail',
                             'message': message})
    logging.info('room:%s' % roomID);
    logging.info('url:%s' % url)
    logging.info('data:%s' % data)
    return json.loads(urllib2.urlopen(url, data).read())

class EmailReceivedHandler(InboundMailHandler):

    ''' receives inbound email, logs it, stores the contents, then forwards to HipChat using the API. '''
    def receive(self, mail_message):
        logging.info ('Received email from %s' % mail_message.sender) 
        ''' TODO: add in exception handling '''
        email = models.EmailNotification()
        email.email_sender = mail_message.sender
        email.email_subject = mail_message.subject
        ''' HACK ALERT '''
        bodies = mail_message.bodies(0)
        for content_type, body in bodies:
           email.email_body = body.decode()
        email.put()
	logging.info('rawto %s' % mail_message.to)
	try:
		regex = re.compile(".*<(.*)-hipmail@uits-eas.appspotmail.com>$")
		r = regex.search(mail_message.to)
		roomName = r.group(1)
		logging.info('roomname %s' % roomName)
		roomID = settings.rooms[roomName] 
	except:
		roomID = settings.rooms['hipmail']

        ''' sends the notification, including a link to the email.'''
        notification = '%s [<a href=\'http://uits-eas.appspot.com/message/%s\'>view</a>]' % (email.email_subject, email.key().id_or_name()) 
        logging.info ('Sending HipChat notification: %s' % sendNotification ( mail_message.sender, notification, roomID )) 
	''' logging.info ('room %s' % roomName)
	logging.info ('roomid %s' % roomID) '''

def main():
    application = webapp.WSGIApplication([EmailReceivedHandler.mapping()], debug=True)        
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()


