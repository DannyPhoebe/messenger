import json
import os
import logging
import webapp2
import requests
import requests_toolbelt.adapters.appengine

requests_toolbelt.adapters.appengine.monkeypatch()

class MainPage(webapp2.RequestHandler):
    def get(self):
        if self.request.get("hub.mode") == "subscribe" and self.request.get("hub.challenge"):
            if self.request.get("hub.verify_token") == '1234':
                self.response.write(self.request.get("hub.challenge"))
            else:
                self.abort(403)



    def post(self):

    # endpoint for processing incoming messaging events

    data = self.request
    logging.info(data)
    #if data["object"] == "page":
    #    for entry in data["entry"]:
    #        for messaging_event in entry["messaging"]:
    #            if messaging_event.get("message"):  # someone sent us a message

    #                sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
    #                recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
    #                message_text = messaging_event["message"]["text"]  # the message's text

    #                send_message(sender_id, "roger that!")

    #            if messaging_event.get("delivery"):  # delivery confirmation
    #                pass

    #            if messaging_event.get("optin"):  # optin confirmation
    #                pass

    #            if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
    #                pass

    self.response.write(200)


    #def send_message(self, recipient_id, message_text):
    #
    #    logging.info("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))
    #    params = {
    #        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    #    }
    #    headers = {
    #        "Content-Type": "application/json"
    #    }
    #    data = json.dumps({
    #        "recipient": {
    #            "id": recipient_id
    #        },
    #        "message": {
    #            "text": message_text
    #        }
    #    })
    #    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    #    if r.status_code != 200:
    #        logging.info(r.status_code)
    #        logging.info(r.text)

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)

