# -*- coding: utf-8 -*-

import json
import re
import os
import logging
import webapp2
import traceback
import urlparse
#from hashlib import pbkdf2_hmac

import cloudstorage as gcs


import crawler_api
import ndb_utils
import send_api

#requests_toolbelt.adapters.appengine.monkeypatch()

class MainPage(webapp2.RequestHandler):
    def get(self):
        if self.request.get("hub.mode") == "subscribe" and self.request.get("hub.challenge"):
            if self.request.get("hub.verify_token") == '1234':
                self.response.write(self.request.get("hub.challenge"))
            else:
                self.abort(403)
        else:
            self.response.write("Hello World")

    def post(self):
        data = json.loads(self.request.body)
        logging.info("Request body:{}".format(data))
        if data["object"] == "page":
            for entry in data["entry"]:
                for messaging_event in entry["messaging"]:
                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    if messaging_event.get("message"):  # someone sent us a message
                        send_api.send_action(sender_id, "mark_seen")
                        send_api.send_action(sender_id, "typing_on")
                        return
                        #message_text = messaging_event["message"]["text"]  # the message's text
#                        urls = []
                        if messaging_event["message"].get("attachments"):  # send via share button
                            attachments = messaging_event["message"]["attachments"]
                            for att in attachments:
                                if att["type"] in ["fallback", "template"]:
                                    parsed = urlparse.urlparse(att["url"])
                                    url = urlparse.parse_qs(parsed.query)["u"][0]
#                                    urls.append(url)
                                else:
                                    send_api.send_message(sender_id, "目前追價弓只接受amazon的商品頁面！")
                                    return
                        elif messaging_event["message"].get("nlp") and messaging_event["message"]["nlp"]["entities"].get("url"):  # send by messaging url directly
                            entities = messaging_event["message"]["nlp"]["entities"]
                            for url in entities.get("url"):
                                if url["domain"] in ["amazon.com", "amazon.co.jp"]:
                                    url = url["value"]
                            else:
                                send_api.send_message(sender_id, "目前追價弓只接受amazon的商品頁面！")
                                return
                        else:
                            send_api.send_message(sender_id, "請分享/貼上amazon商品頁面，讓追價弓為您掌握良機！")
                            return
                        meta = crawler_api.get_meta(url)
                        logging.info(meta)
                        bucket = "amazon_price_history"
                        try:
                            f = gcs.open("/" + os.path.join(bucket, meta["asin"]))
                            current, lowest, history = json.loads(f.read())
                            logging.info("existed")
                        except:
                            current, lowest, history = crawler_api.get_stat(url)
                            with gcs.open("/" + os.path.join(bucket, meta["asin"]), "w") as o:
                                o.write(json.dumps([current, lowest, history ]))
                            logging.info("crawling")

                        user_key = ndb_utils.create_user_entity(uid=sender_id)
                        logging.info("user_key: {}".format(user_key))
                        product_key = ndb_utils.create_product_entity(url, current, lowest, history, meta)
                        logging.info("product_key: {}".format(product_key))
                        monitor_key = ndb_utils.create_monitor_entity(user_key.id(), product_key.id(), current)
                        logging.info("monitor_key: {}".format(monitor_key))
                        currency="$"
                        send_api.send_generic_template(
                            sender_id,
                            meta,
                            "現價: {symbl}{cur}\n最低: {symbl}{low}\n可省: {symbl}{bft}({pct}%)".format(symbl=currency, cur=current, low=lowest, bft=(lowest-current) if lowest != "N/A" else "N/A",  pct=round((lowest-current)*100/current,1) if lowest != "N/A" else "N/A"),
                            monitor_key.urlsafe()
                        )
#                                    if "Amazon Price History" in price_stat:
#                                        hist = price_stat["Amazon Price History"][0] # 0: HLCA, 1: last modified
#                                    elif "3rd Party New Price History" in price_stat:
#                                        hist = price_stat["3rd Party New Price History"][0]
#                                    else:
#                                        logging.warning("No price data found: {}".format(product_key))
#                                        send_api.send_message(sender_id, "Oops! 追價弓維修中")
#                                        return 
#                                    low = hist["Lowest"][0] if "Lowest" in hist else "N/A"
#                                    cur = hist["Current"][0]
#                                    monitor_key = create_monitor_entity(uid=sender_id, product_key=product_key.urlsafe(), threshold=cur)


                                    #price_stat = self.get_price_stat(url["domain"], url["value"])
#                        except:
#                            logging.warning(traceback.format_exc())

                    if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                        send_api.send_action(sender_id, "mark_seen")
                        send_api.send_action(sender_id, "typing_on")
                        title = messaging_event["postback"]["title"]
                        payload = json.loads(messaging_event["postback"]["payload"])
                        if title == u"追價":
                            monitor = ndb_utils.fetch_by_urlsafe_key(payload["key"])
                            if ndb_utils.has_quota(monitor.user):
                                monitor.switch = True
                                monitor.put()
                                send_api.send_message(sender_id, "鎖定!")
                            else:
                                send_api.send_charge_template(sender_id)
                        if title == u"移除":
                            monitor = ndb_utils.fetch_by_urlsafe_key(payload["key"])
                            if monitor.switch:
                                monitor.switch = False
                                monitor.put()
                                send_api.send_message(sender_id, "釋放quota")
#                            else:
#                                send_api.send_message(sender_id, "已不存在")
                        if title == u"取得更多quota":
                            pass
                        if title == u"檢視我的追價":
                            collection = ndb_utils.get_monitoring(sender_id)
                            send_api.send_collection_template(sender_id, collection)

                    if messaging_event.get("delivery"):  # delivery confirmation
                        pass

                    if messaging_event.get("optin"):  # optin confirmation
                        pass

app = webapp2.WSGIApplication([
    ('/', MainPage),
], debug=True)

