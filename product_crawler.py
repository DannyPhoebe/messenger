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
from ndb_utils import create_monitor_entity, create_product_entity, fetch_by_key, monitor_quota, get_monitoring

requests_toolbelt.adapters.appengine.monkeypatch()

#    def send_message(self, recipient_id, message_text):
#        logging.info("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))
#        params = {
#            "access_token": os.environ["PAGE_ACCESS_TOKEN"],
#        }
#        headers = {
#                "Content-Type": "application/json"
#        }
#        data = json.dumps({
#            "recipient": {
#                "id": recipient_id
#            },
#            "message": {
#                "text": message_text
#            }
#        })
        #batch=[{"method":"GET", "relative_url":"me/messages?recipient={id={}}&message={text={}},{"method":"GET", "relative_url":"me/messages"}]'
#        r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
#        if r.status_code != 200:
#            logging.info(r.status_code)
#            logging.info(r.text)

    def get_price_stat(self, product_key):
#        def stat_format(stat_pane):
#            tds = stat_pane.select("td")
#            result = dict()
#            for idx in range(0, len(tds), 3):
#                tag, value, ts = tds[idx: idx+3]
#                result.update({re.search("\w+", tag.text).group(0): (value.text.strip(), ts.text.strip())})
#            return result
#        
#        def history_format(history_pane):
#            tds = history_pane.select("td")
#            result = dict()
#            for num, idx in enumerate(range(0, len(tds), 2)):
#                ts, value = tds[idx: idx+2]
#                result[num] = (value.text.strip(), ts.text.strip())
#            return result
#        from bs4 import BeautifulSoup
#        header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36"}
#        api_addr = "https://camelcamelcamel.com/search"
#        res = requests.get(api_addr, params={"sq": url}, headers=header)
#        assert res.status_code == 200
#        soup = BeautifulSoup(res.text, "lxml")
#        panes = soup.select(".product_pane")
#        price_data = dict()
#        for idx in range(0, len(panes), 2):
#            stat_pane, history_pane = panes[idx:idx+2]
#            provider = stat_pane.find_previous_sibling('h3').text
#            price_data.update({provider: [stat_format(stat_pane), history_format(history_pane)]})
#        return price_data
        
        product = fetch_by_key(product_key)
        api_addr = "https://us-central1-prime-basis-152406.cloudfunctions.net/stat_crawler"        
        new_price = requests.post(api_addr, json={"url": product.link})
        product.price = new_price
        product = product.put()
        logging.info("update {} price data succuessfully".format(product_key))
        if "Amazon Price History" in new_price:
            hist = price_stat["Amazon Price History"][0] # 0: HLCA, 1: last modified
            cur = float(hist["Current"][0][1:].replace(",",""))
        elif "3rd Party New Price History" in new_price:
            hist = price_stat["3rd Party New Price History"][0]
            cur = float(hist["Current"][0][1:].replace(",",""))
            
        triggered = get_triggered_alert(product_key, cur)
        self.send_alert(sender_id, product, current)

    def send_alert(self, recipient_id, product, monitor):
        logging.info("sending alert to {recipient}".format(recipient=recipient_id))
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
                                "title": product.meta["alt"],
                                "image_url": product.meta["img"],
                                "subtitle": "Current: {symbl}{cur}\nAlert: {symbl}{thd}\nSave: {symbl}{save}({pct}%)".format(symbl=product.price["symbol"], cur=cur, thd=monitor.threshold, save=product-monitor.threshold if low != "N/A" else "N/A",  pct=round((cur-low)*100/cur,1) if low != "N/A" else "N/A"), # drop
                                "default_action": {
                                    "type": "web_url",
                                    "url": product.link,
                                    "webview_height_ratio": "full",
                                    "messenger_extensions": False,/"
                                }, # end of default_action
                                "buttons":[
                                    # b1
                                    {
                                        "type": "postback",
                                        "title": "keep alert",
                                        "payload": json.dumps(
                                            {
                                                "key": monitor.key.urlsafe()
                                            }
                                        )
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

            
class ProductCrawler(webapp2.RequestHandler):
    def get(self):
        url = self.request.get("url", None)
        if url is not None:
        
                self.response.write(200)
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
                                    if att["type"] in  ["fallback", "template"]:
                                        self.send_action(sender_id, "mark_seen")
                                        self.send_action(sender_id, "typing_on")
                                        parsed = urlparse.urlparse(att["url"])
                                        url = urlparse.parse_qs(parsed.query)["u"][0]
                                        price_stat = self.get_price_stat(url)
                                        meta = self.get_metadata(url)
                                        product_key = create_product_entity(link=url, price=price_stat, meta=meta)
                                        logging.info("product_key: {}".format(product_key))
                                        if "Amazon Price History" in price_stat:
                                            hist = price_stat["Amazon Price History"][0] # 0: HLCA, 1: last modified
                                            low = float(hist["Lowest"][0][1:].replace(",","")) if "Lowest" in hist else "N/A"
                                            cur = float(hist["Current"][0][1:].replace(",",""))
                                            symbl = hist["Current"][0][0].encode("utf-8")
                                        elif "3rd Party New Price History" in price_stat:
                                            hist = price_stat["3rd Party New Price History"][0]
                                            low = float(hist["Lowest"][0][1:].replace(",","")) if "Lowest" in hist else "N/A"
                                            cur = float(hist["Current"][0][1:].replace(",",""))
                                            symbl = hist["Current"][0][0].encode("utf-8")
                                        else:
                                            logging.warning("No price data found: {}".format(product_key))
                                            self.send_message(sender_id, "Ohoh! Something Wrong")
                                            return 
                                        monitor_key = create_monitor_entity(uid=sender_id, product_key=product_key.urlsafe(), threshold=cur)
                                        logging.info("monitor_key: {}".format(monitor_key))                                        
                                        self.send_generic_template(
                                            sender_id,
                                            meta,
                                            "Current: {symbl}{cur}\nLowest: {symbl}{low}\nBenefit: {symbl}{bft}({pct}%)".format(symbl=symbl, cur=cur, low=low, bft=cur-low if low != "N/A" else "N/A",  pct=round((cur-low)*100/cur,1) if low != "N/A" else "N/A"),
                                            monitor_key.urlsafe()
                                        )
                            elif messaging_event["message"].get("nlp"):
                                entities = messaging_event["message"]["nlp"]["entities"]
                                urls = entities.get("url")
                                for url in urls:
                                    if url["domain"] in ["amazon.com", "amazon.co.jp"]:
                                        self.send_action(sender_id, "mark_seen")
                                        self.send_action(sender_id, "typing_on")
                                        url = url["value"]
                                        #price_stat = self.get_price_stat(url["domain"], url["value"])
                                        price_stat = self.get_price_stat(url)
                                        meta = self.get_metadata(url)
                        except:
                            logging.warning(traceback.format_exc())

                    if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                        title = messaging_event["postback"]["title"]
                        payload = json.loads(messaging_event["postback"]["payload"])
                        if title == "set price alert":
                            monitor = fetch_by_key(payload["key"])
                            if monitor_quota(monitor.uid):
                                monitor.switch = True
                                monitor.put()
                                self.send_message(sender_id, "got it!")
                            else:
                                self.send_charge_template(sender_id)
                        if title == "remove":
                            monitor = fetch_by_key(payload["key"])
                            if monitor.switch:
                                monitor.switch = False
                                monitor.put()
                                self.send_message(sender_id, "release 1 quota")
                            else:
                                self.send_message(sender_id, "already removed")
                        if title == "more quota":
                            pass
                        if title == "view my alerts":
                            self.send_collection_template(sender_id)

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
                                                                    "title":"create your alerts",
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

    def element_builder(self, monitor_entity):
        target = fetch_by_key(monitor_entity.target)
        element = {
            "title": target.meta["alt"],
            "image_url": target.meta["img"],
            "subtitle": "setting: {}".format(monitor_entity.threshold),
            "default_action": {
                "type": "web_url",
                "url": target.link,
                "webview_height_ratio": "full",
                "messenger_extensions": False,
                #"fallback_url": "https://petersfancybrownhats.com/"
            }, # end of default_action
            "buttons":[
                # b1
                {
                     "type": "postback",
                     "title": "remove",
                     "payload": json.dumps(
                         {
                             "key": monitor_entity.key.urlsafe()
                         }
                     )
                },
#                # b2
#                {
#                     "type": "element_share",
#               },
            ] # end of buttons
        } # end of elements
        return element

    def send_collection_template(self, recipient_id):
        logging.info("sending collection to {recipient}".format(recipient=recipient_id))
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
                        "elements": [self.element_builder(item) for item in get_monitoring(recipient_id)]   
                    } # end of payload
                } # end of attachment
            } # end of message
        })
        r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
        if r.status_code != 200:
            logging.info(r.status_code)
            logging.info(r.text)

    def send_charge_template(self, recipient_id):
        logging.info("sending charge to {recipient}".format(recipient=recipient_id))
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
                        "template_type":"button",
                        "text": "Oops! Run out of free alert quota",
                        "buttons": [
                            # b1
                            {
                                 "type": "postback",
                                 "title": "more quota",
                                 "payload": json.dumps(
                                     {
                                         "key": "buy"
                                     }
                                 )
                            },
                            # b2
                            {
                                 "type": "postback",
                                 "title": "view my alerts",
                                 "payload": json.dumps(
                                     {
                                         "key": "collection"
                                     }
                                 )
                            }
                        ]
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
        meta = {
            "asin": soup.select("#ASIN")[0]["value"],
            "alt": img["alt"],
            "img": img["data-old-hires"]
            #"img": json.loads(img["data-a-dynamic-image"]).keys()[0]
        }
        logging.info(meta)
        return meta

    def get_price_stat(self, url):
        def stat_format(stat_pane):
            tds = stat_pane.select("td")
            result = dict()
            for idx in range(0, len(tds), 3):
                tag, value, ts = tds[idx: idx+3]
                result.update({re.search("\w+", tag.text).group(0): (value.text.strip(), ts.text.strip())})
            return result
        
        def history_format(history_pane):
            tds = history_pane.select("td")
            result = dict()
            for num, idx in enumerate(range(0, len(tds), 2)):
                ts, value = tds[idx: idx+2]
                result[num] = (value.text.strip(), ts.text.strip())
            return result
        from bs4 import BeautifulSoup
        header = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.87 Safari/537.36"}
#        api_addr = {
#            "amazon.com": "https://camelcamelcamel.com/search",
#            "amazon.co.jp":"https://jp.camelcamelcamel.com/search"
#        }
        api_addr = "https://camelcamelcamel.com/search"
        res = requests.get(api_addr, params={"sq": url}, headers=header)
        assert res.status_code == 200
        soup = BeautifulSoup(res.text, "lxml")
        panes = soup.select(".product_pane")
        price_data = dict()
        for idx in range(0, len(panes), 2):
            stat_pane, history_pane = panes[idx:idx+2]
            provider = stat_pane.find_previous_sibling('h3').text
            price_data.update({provider: [stat_format(stat_pane), history_format(history_pane)]})
        return price_data
        
        #row_in_table = soup.select(".product_pane > tbody")[0].select("tr")
        #return "\n".join([" ".join([val.text for val in prop.select("td")]) for prop in row_in_table]).encode("utf-8")


app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)

