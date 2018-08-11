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

if __name__ == '__main__':
    pass
