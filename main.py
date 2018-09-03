# -*- coding: utf-8 -*-

import json
import re
import os
import logging
import webapp2
import traceback
from urlparse import urlparse, parse_qs
#from urllib.parse import urlparse, parse_qs
#from hashlib import pbkdf2_hmac


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
#                        return
                        #message_text = messaging_event["message"]["text"]  # the message's text
                        user_key = ndb_utils.create_user_entity(uid=sender_id)
                        logging.info("user_key: {}".format(user_key))
                        if messaging_event["message"].get("nlp"):
                            if messaging_event["message"]["nlp"]["entities"].get("url"):  # send by messaging url directly
                                entities = messaging_event["message"]["nlp"]["entities"]
                                for url in entities.get("url"):
                                    logging.info(url["domain"])
                                    if url["domain"] in ["amazon.com", "amazon.co.jp"]:
                                        domain = url["domain"]
                                        url = url["value"]
                                    else:
                                        send_api.send_message(sender_id, "目前追價弓只接受amazon的商品頁面")
                                        return
                            else:
                                #send_api.send_tutorial(sender_id)
                                send_api.send_message(sender_id, "請分享/貼上amazon商品頁面，用追價弓掌握低價良機！")
                                return
                        elif messaging_event["message"].get("attachments"):  # send via share button
                            attachments = messaging_event["message"]["attachments"]
                            for att in attachments:
                                if att["type"] in ["fallback", "template"]:
                                    parsed = urlparse(att["url"])
                                    url = parse_qs(parsed.query)["u"][0]
                                    amazon_domain = re.search("amazon.com|amazon.co.jp", url)
                                    if amazon_domain:
                                        domain = amazon_domain.group(0)
                                    else:
                                        send_api.send_message(sender_id, "目前追價弓只接受amazon的商品頁面")
                                        return
                                else:
                                    send_api.send_message(sender_id, "目前追價弓只接受amazon的商品頁面")
                                    return
                        else:
                            send_api.send_message(sender_id, "請分享/貼上amazon商品頁面，用追價弓掌握低價良機！")
                            return
                        found_asin = re.search("\/([0-9A-Z]{10})[/?]", url)
                        if not found_asin:
                            send_api.send_message(sender_id, "Oops! 商品頁面不存在")
                            return
                        else:
                            asin = found_asin.group(1)
                            product_entity = ndb_utils.fetch_by_urlsafe_key(asin, urlsafe=False)
                            currency = {"amazon.com":"$", "amazon.co.jp":"¥"}
                            if product_entity:
                                meta = product_entity.meta
                                history = product_entity.history
                                current, lowest = crawler_api.stat_parser(history)
                                diff = lowest - current if current and lowest else "N/A"
                                product_key = product_entity.key
                            else:
                                info = crawler_api.get_product_info(url)
                                if not info:
#                                    send_api.send_message(sender_id, "Oops! 追價弓異常，請鎖定其他商品")
                                    send_api.send_message(sender_id, "Sorry！此商品無法追價，請鎖定其他商品")
                                    return 
                                meta, history = info
                                current, lowest = crawler_api.stat_parser(history)
                                diff = lowest - current if current and lowest else "N/A"
                                product_key = ndb_utils.create_product_entity(url, current, lowest, history, meta)
                            logging.info("product_key: {}".format(product_key))
                            monitor_key = ndb_utils.create_monitor_entity(user_key.id(), product_key.id(), current)
                            logging.info("monitor_key: {}".format(monitor_key))
                            send_api.send_generic_template(
                                sender_id,
                                url,
                                meta,
                                "現價: {symbl}{cur}\n最低: {symbl}{low}\n變動: {symbl}{diff}({pct}%)".format(symbl=currency[domain], cur=current if current else "N/A", low=lowest if lowest else "N/A", diff=diff,  pct=round(diff*100/current, 1) if lowest else ""),
                                monitor_key.urlsafe()
                            )
                            
                    if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                        send_api.send_action(sender_id, "mark_seen")
                        send_api.send_action(sender_id, "typing_on")
                        title = messaging_event["postback"]["title"]
                        payload = json.loads(messaging_event["postback"]["payload"])
                        if title == "get_started":
                            user_key = ndb_utils.create_user_entity(uid=sender_id)
                            send_api.send_tutorial(sender_id)
                        if title == u"追價":
                            monitor = ndb_utils.fetch_by_urlsafe_key(payload["key"])
                            if not monitor.switch:
                                if ndb_utils.has_quota(monitor.user):
                                    monitor.switch = True
                                    monitor.put()
                                    send_api.send_message(sender_id, "商品降價立刻通知你！")
                                else:
                                    send_api.send_charge_template(sender_id)
                            else:
                                send_api.send_message(sender_id, "已在追價清單中")

                        if title == u"移除":
                            monitor = ndb_utils.fetch_by_urlsafe_key(payload["key"])
                            if monitor.switch:
                                monitor.switch = False
                                monitor.put()
                                send_api.send_message(sender_id, "釋放quota")
                            else:
                                send_api.send_message(sender_id, "已不在追價清單中")
                        if title == u"等待更低價":
                            monitor = ndb_utils.fetch_by_urlsafe_key(payload["key"])
                            product = ndb_utils.fetch_by_urlsafe_key(monitor.target, urlsafe=False)
                            monitor.threshold = product.current
                            monitor.put()
                            send_api.send_message(sender_id, "有更低價立刻通知你！")
                        if title == u"取得更多quota":
                            send_api.send_message(sender_id, "追價弓一瞬間發出藍色的光芒！(beta)")
                        if title == u"檢視我的追價":
                            collection = ndb_utils.get_monitoring(sender_id)
                            if collection:
                                send_api.send_collection_template(sender_id, collection)
                            else:
                                send_api.send_message(sender_id, "追價弓正蓄勢待發！")

                    if messaging_event.get("delivery"):  # delivery confirmation
                        pass

                    if messaging_event.get("optin"):  # optin confirmation
                        pass

class UpdateManager(webapp2.RequestHandler):
    def get(self):
        from google.appengine.api import taskqueue
        products = ndb_utils.get_all_products()        
        for idx, p in enumerate(products):
            task = taskqueue.add(
                queue_name="update",
                method="POST",
                url='/history/manage',
                params={
                    "urlsafe_key": p.key.urlsafe()                    
                },
                #countdown = randint(0, 600)
            )
        logging.info("{} products are waiting for update".format(idx))
    
    def post(self):
        from google.appengine.api import taskqueue
        key = self.request.get("urlsafe_key")        
        product_entity = ndb_utils.fetch_by_urlsafe_key(key)
        info = crawler_api.get_product_info(product_entity.link)
        if not info:
            logging.warning("{} update failed".format(product_entity.key.id()))
            return 
        meta, history = info
        current, lowest = crawler_api.stat_parser(history)
        add_alert = current != product_entity.current 
        logging.info("b:{} a:{}".format(product_entity.current, current)) 
        product_entity.current = current
        product_entity.lowest = lowest
        product_entity.history = history
        product_entity.put()
        if add_alert:
            task = taskqueue.add(
                queue_name="alert",
                method="POST",
                url='/alert',
                params={
                    "urlsafe_key": key                    
                },
            )
        logging.info("{} update complete".format(product_entity.key.id()))

class AlertManager(webapp2.RequestHandler):
    def get(self):
        self.response.write("Hello World")
        
    def post(self):
        key = self.request.get("urlsafe_key")
        product_entity = ndb_utils.fetch_by_urlsafe_key(key)
        current, lowest = crawler_api.stat_parser(product_entity.history)
        product_key = product_entity.key
        monitor_entitys = ndb_utils.touch_alert(product_key)
        for touched in monitor_entitys:
            alert = touched.threshold
            diff = current - alert
            send_api.send_alert_template(
                touched.user,
                product_entity.link,
                product_entity.meta,
                "鎖定: {symbl}{alert}\n現價: {symbl}{cur}\n降價: {symbl}{diff}({pct}%)".format(symbl=currency[domain], cur=current, alert=alert, diff=diff, pct=round(diff*100/alert, 1)),
                monitor_key.urlsafe()
            )

class PolicyPage(webapp2.RequestHandler):
    def get(self):
        self.response.write("follow GDPR")


app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/history/manage', UpdateManager),
    ('/alert', AlertManager),
    ('/privacy_policy', PolicyPage),
], debug=True)

