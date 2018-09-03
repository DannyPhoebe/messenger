# -*- coding: utf-8 -*-

import logging
import requests
import requests_toolbelt.adapters.appengine
import traceback

from google.appengine.api import urlfetch

requests_toolbelt.adapters.appengine.monkeypatch()
urlfetch.set_default_fetch_deadline(60)

def get_stat(url):
    api_addr = "https://us-central1-prime-basis-152406.cloudfunctions.net/stat_crawler"
    r = requests.post(api_addr, json={"url":url}, timeout=60)
    if r.status_code == 200:
        return r.json()

def get_meta(url):
    api_addr = "https://us-central1-prime-basis-152406.cloudfunctions.net/meta_crawler"
    r = requests.post(api_addr, json={"url":url}, timeout=60)
    if r.status_code == 200:
        return r.json()

def get_product_info(url):
    api_addr = "https://us-central1-prime-basis-152406.cloudfunctions.net/product_info_crawler"
    r = requests.post(api_addr, json={"url":url}, timeout=60)
    if r.status_code == 200:
        try:
            return r.json()
        except:
            return
        
#def async_request(url):
#    rpc = urlfetch.create_rpc()
#    urlfetch.make_fetch_call(rpc, url)
#    return rpc


def stat_parser(price_stat):
    current = None
    lowest = None
    for provider in ["3rd Party New Price History", "Amazon Price History"]:
        if provider in price_stat:
            currency = price_stat[provider][0]["Current"][0][0]
            if "Current" in price_stat[provider][0] and price_stat[provider][0]["Current"][0] != "Not in Stock":
                tmp = float(price_stat[provider][0]["Current"][0][1:].replace(",",""))
                if not current or tmp < current:
                    current = tmp
            if "Lowest" in price_stat[provider][0]:
                tmp = float(price_stat[provider][0]["Lowest"][0][1:].replace(",",""))
                if not lowest or tmp < lowest:
                    lowest = tmp
    return current, lowest
    
if __name__ == '__main__':
    pass
