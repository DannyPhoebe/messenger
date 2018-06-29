# -*- coding: utf-8 -*-

import json
import re
import os
import logging
import webapp2
import requests
import requests_toolbelt.adapters.appengine
import traceback
import urlparse
#from hashlib import pbkdf2_hmac

from model import Monitor, Product
from ndb_utils import create_monitor_entity, create_product_entity, fetch_by_key

requests_toolbelt.adapters.appengine.monkeypatch()

class MainPage(webapp2.RequestHandler):
    def get(self):
        if self.request.get("hub.mode") == "subscribe" and self.request.get("hub.challenge"):
            if self.request.get("hub.verify_token") == '1234':
                self.response.write(self.request.get("hub.challenge"))
            else:
                self.abort(403)

    def post(self):
        data = json.loads(self.request.body)
        logging.info(data)
        if data["object"] == "page":
            for entry in data["entry"]:
                for messaging_event in entry["messaging"]:
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    if messaging_event.get("message"):  # someone sent us a message
                        #message_text = messaging_event["message"]["text"]  # the message's text
                        try:
                            if messaging_event["message"].get("attachments"):
                                attachments = messaging_event["message"]["attachments"]
                                for att in attachments:
                                    if att["type"] == "fallback":
                                        self.send_action(sender_id, "mark_seen")
                                        self.send_action(sender_id, "typing_on")
                                        parsed = urlparse.urlparse(att["url"])
                                        url = urlparse.parse_qs(parsed.query)["u"][0]
                                        price_stat = self.get_price_stat("amazon.com", url)
                                        meta = self.get_metadata(url)
                                        product_key = create_product_entity(link=url, highest=100, lowest=50, current=[(55,1530242624)], meta=meta)
                                        logging.info("ppp")
                                        logging.info(product_key)
                                        #product_key = self.create_product_entity(id=meta["asin"], link=url, highest=highest, lowest=lowest, current=current)
                                        monitor_key = create_monitor_entity(uid=sender_id, product=product_key.get())
                                        logging.info("mmm")
                                        logging.info(monitor_key)
                                        self.send_generic_template(sender_id, meta, price_stat, monitor_key.urlsafe())
                            elif messaging_event["message"].get("nlp"):
                                entities = messaging_event["message"]["nlp"]["entities"]
                                urls = entities.get("url")
                                for url in urls:
                                    if url["domain"] in ["amazon.com", "amazon.co.jp"]:
                                        self.send_action(sender_id, "mark_seen")
                                        self.send_action(sender_id, "typing_on")
                                        url = url["value"]
                                        #price_stat = self.get_price_stat(url["domain"], url["value"])
                                        price_stat = self.get_price_stat("amazon.com", url)
                                        meta = self.get_metadata(url)
                        except:
                            logging.warning(traceback.format_exc())

                    if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                        payload = json.loads(messaging_event["postback"]["payload"])
                        monitor = fetch_by_key(payload["key"])
                        monitor.switch = True
                        monitor.put()
                        #query = fetch_by_key(alert_data["key"])
                        #query.alert = True
                        #query.put()
                        self.send_message(sender_id, "roger that!")

                    if messaging_event.get("delivery"):  # delivery confirmation
                        pass

                    if messaging_event.get("optin"):  # optin confirmation
                        pass


    def send_message(self, recipient_id, message_text):
        logging.info("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))
        params = {
            "access_token": os.environ["PAGE_ACCESS_TOKEN"],
            #"appsecret_proof": pbkdf2_hmac('sha256', os.environ["PAGE_ACCESS_TOKEN"], os.environ["APP_SECRET"], 100000)
        }
        headers = {
                "Content-Type": "application/json"
        }
        data = json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "text": message_text
            }
        })
        r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
        if r.status_code != 200:
            logging.info(r.status_code)
            logging.info(r.text)

    def send_action(self, recipient_id, action):
        logging.info("sending {action} to {recipient}".format(action=action, recipient=recipient_id))
        params = {
            "access_token": os.environ["PAGE_ACCESS_TOKEN"],
        }
        headers = {
                "Content-Type": "application/json"
        }
        data = json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "sender_action": action
        })
        r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
        if r.status_code != 200:
            logging.info(r.status_code)
            logging.info(r.text)

    def send_generic_template(self, recipient_id, meta, price_stat, monitor_key):
        logging.info("sending generic_template to {recipient}".format(recipient=recipient_id))
        params = {
            "access_token": os.environ["PAGE_ACCESS_TOKEN"],
        }
        headers = {
            "Content-Type": "application/json"
        }
        data = json.dumps({
            "recipient": {
                "id": recipient_id
            },
            "message": {
                "attachment": {
                    "type":"template",
                    "payload":{
                        "template_type":"generic",
                        "sharable": "true",
                        "elements":[
                            {
                                "title": meta["alt"],
                                "subtitle": price_stat,
                                "buttons":[
                                    # b1
                                    {
                                        "type": "postback",
                                        "title": "set price alert",
                                        "payload": json.dumps(
                                            {
                                                "key": monitor_key
                                            }
                                        )
                                    },
                                    # b2
                                    #{
                                    #    "type": "web_url",
                                    #    "url": "https://www.amazon.co.jp",
                                    #    "title": "buy it",
                                    #},
                                    # b3
                                    {
                                        "type":"element_share",
                                        "share_contents": {
                                            "attachment": {
                                                "type": "template",
                                                "payload":{
                                                    "template_type":"generic",
                                                    "sharable": "true",
                                                    "elements":[
                                                        {
                                                            "title": meta["alt"],
                                                            "image_url": meta["img"],
                                                            "subtitle": price_stat,
                                                            "default_action": {
                                                                "type": "web_url",
                                                                "url": "https://www.amazon.co.jp",
                                                                "webview_height_ratio": "tall",
                                                                "messenger_extensions": False,
                                                                #"fallback_url": "https://petersfancybrownhats.com/"
                                                            }, # end of default_action
                                                            "buttons":[
                                                                # b1
                                                                {
                                                                    "type": "web_url",
                                                                    #"url": "https://www.facebook.com/卡喜多-Cardcito-166640317462344/",
                                                                    "url": "https://m.me/166640317462344",
                                                                    "title":"create your collection",
                                                                },
                                                            ] # end of buttons
                                                        } # end of elements
                                                    ] # end of elements
                                                } # end of payload
                                            } # end of attachment
                                        } # end of ahare_contents
                                    }
                                ] # end of buttons
                           } # end of elements
                        ] # end of elements      
                    } # end of payload
                } # end of attachment
            } # end of message
        })
        r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
        if r.status_code != 200:
            logging.info(r.status_code)
            logging.info(r.text)


    def get_metadata(self, url):
        import requests
        from bs4 import BeautifulSoup
        header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36"}
        res = requests.get(url, headers=header)
        assert res.status_code == 200
        soup = BeautifulSoup(res.text, "lxml")
        #meta = {"asin": re.search("dp/([A-Z0-9]+?)/", url).group(1)}
        img = soup.select("#landingImage")[0]
        meta = {"asin": soup.select("#ASIN")[0]["value"],
                "alt": img["alt"],
                "img": img["data-old-hires"]
                #"img": json.loads(img["data-a-dynamic-image"]).keys()[0]
        }
        logging.info(meta)
        return meta

    def get_price_stat(self, domain, url):
        import requests
        from bs4 import BeautifulSoup
        header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36"}
        api_addr = {
            "amazon.com": "https://camelcamelcamel.com/search",
            "amazon.co.jp":"https://jp.camelcamelcamel.com/search"
        }
        res = requests.get(api_addr[domain], params={"sq": url}, headers=header)
        assert res.status_code == 200
        soup = BeautifulSoup(res.text, "lxml")
        row_in_table = soup.select(".product_pane > tbody")[0].select("tr")
        return "\n".join([" ".join([val.text for val in prop.select("td")]) for prop in row_in_table]).encode("utf-8")


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)

