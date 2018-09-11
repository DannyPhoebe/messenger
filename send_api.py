# -*- coding: utf-8 -*-

import json
import logging
import os
import time
import requests
import requests_toolbelt.adapters.appengine

requests_toolbelt.adapters.appengine.monkeypatch()

def send_message(recipient_id, message_text):
    logging.info("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))
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
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        logging.info(r.status_code)
        logging.info(r.text)

def send_action(recipient_id, action):
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

def send_example(recipient_id):
    logging.info("sending media_template to {recipient}".format(recipient=recipient_id))
    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"],
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
      "recipient":{
        "id": recipient_id
      },
      "message":{
        "attachment": {
          "type": "template",
          "payload": {
             "template_type": "media",
             "elements": [
                {
                   "media_type": "image",
                   "attachment_id": "291089468172284"
                }
             ]
          }
        }    
      }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        logging.info(r.status_code)
        logging.info(r.text)

def send_tutorial(recipient_id):
    #send_message(recipient_id, "將有興趣的Amazon商品頁面分享給追價弓，或是直接貼上商品網址，立刻取得歷史低價資訊，像這樣：")
    send_message(recipient_id, "分享Amazon商品頁面給我，立刻取得歷史低價資訊")
    send_action(recipient_id, "typing_on")
    time.sleep(2.5)
    send_example(recipient_id)
    send_action(recipient_id, "typing_on")
    time.sleep(2.5)
    send_message(recipient_id, "按下【追價】，每次降價立即通知你！")

def send_generic_template(recipient_id, link, meta, price_stat, monitor_key):
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
                            "image_url": meta["img"],
                            "subtitle": price_stat,
                            "default_action": {
                                "type": "web_url",
                                "url": link,
                                "webview_height_ratio": "full",
                                "messenger_extensions": False,
                                #"fallback_url": "https://petersfancybrownhats.com/"
                            }, # end of default_action
                            "buttons":[
                                # b1
                                {
                                    "type": "postback",
                                    "title": "追價",
                                    "payload": json.dumps(
                                        {
                                            "key": monitor_key
                                        }
                                    )
                                },
                                # b2
                                {
                                    "type": "postback",
                                    "title": "檢視我的追價",
                                    "payload": json.dumps(
                                        {
                                             "key": "collection"
                                        }
                                    )
                                },
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
                                                            "url": link,
                                                            "webview_height_ratio": "full",
                                                            "messenger_extensions": False,
                                                            #"fallback_url": "https://petersfancybrownhats.com/"
                                                        }, # end of default_action
                                                        "buttons":[
                                                            # b1
                                                            {
                                                                "type": "web_url",
                                                                "url": "https://www.facebook.com/Archdown追價弓-651712701861404/",
                                                                #"url": "https://m.me/651712701861404",
                                                                "title":"立刻體驗追價弓",
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

def element_builder(entity_pair):
    from datetime import datetime
    monitor_entity, product_entity = entity_pair
    element = {
        "title": product_entity.meta["alt"],
        "image_url": product_entity.meta["img"],
        "subtitle": "現價: {}{}\n追價天數: {}".format(product_entity.currency.encode("utf-8"), product_entity.current, (datetime.now() - monitor_entity.timestamp).days),
        "default_action": {
            "type": "web_url",
            "url": product_entity.link,
            "webview_height_ratio": "full",
            "messenger_extensions": False,
            #"fallback_url": "https://petersfancybrownhats.com/"
        }, # end of default_action
        "buttons":[
            # b1
            {
                 "type": "postback",
                 "title": "移除",
                 "payload": json.dumps(
                     {
                         "key": monitor_entity.key.urlsafe()
                     }
                 )
            },
        ] # end of buttons
    } # end of elements
    return element

def send_collection_template(recipient_id, collection):
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
                    "elements": [element_builder(pair) for pair in collection]   
                } # end of payload
            } # end of attachment
        } # end of message
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        logging.info(r.status_code)
        logging.info(r.text)

def send_charge_template(recipient_id):
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
                    "text": "Oops! 追價QUOTA已用盡",
                    "buttons": [
                        # b1
                        {
                             "type": "postback",
                             "title": "取得更多QUOTA",
                             "payload": json.dumps(
                                 {
                                     "key": "buy"
                                 }
                             )
                        },
                        # b2
                        {
                             "type": "postback",
                             "title": "檢視我的追價",
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
            
def send_alert_template(recipient_id, link, meta, price_stat, monitor_key):
    logging.info("sending alert_template to {recipient}".format(recipient=recipient_id))
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
                            "title": "《！！！降價通知！！！》\n" + meta["alt"].encode("utf-8"),
                            #"title": meta["alt"],
                            "image_url": meta["img"],
                            "subtitle": price_stat,
                            "default_action": {
                                "type": "web_url",
                                "url": link,
                                "webview_height_ratio": "full",
                                "messenger_extensions": False,
                                #"fallback_url": "https://petersfancybrownhats.com/"
                            }, # end of default_action
                            "buttons":[
                                # b1
                                {
                                    "type": "web_url",
                                    "url": "https://archdown-tracker.appspot.com/redirect?link={link}&key={key}".format(link=link, key=monitor_key),
                                    "title": "前往選購",
                                    "webview_height_ratio": "full",
                                    "messenger_extensions": False,
                                },
                                # b2
                                {
                                     "type": "postback",
                                     "title": "移除",
                                     "payload": json.dumps(
                                         {
                                             "key": monitor_key
                                         }
                                     )
                                },
                                # b3
                                {
                                     "type": "postback",
                                     "title": "等待更低價",
                                     "payload": json.dumps(
                                         {
                                             "key": monitor_key
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

if __name__ == '__main__':
    pass
