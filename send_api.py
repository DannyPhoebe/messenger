# -*- coding: utf-8 -*-

import json
import logging
import os
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

def send_generic_template(recipient_id, meta, price_stat, monitor_key):
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
                                    "title": "追價",
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
    monitor_entity, target_entity = entity_pair
    element = {
        "title": target_entity.meta["alt"],
        "image_url": target_entity.meta["img"],
        "subtitle": "現價: {}".format(target_entity.current),
        "default_action": {
            "type": "web_url",
            "url": target_entity.link,
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
                    "text": "Oops! 追價quota已用盡",
                    "buttons": [
                        # b1
                        {
                             "type": "postback",
                             "title": "取得更多 quota",
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
            

if __name__ == '__main__':
    pass
