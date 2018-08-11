# -*- coding: utf-8 -*-

from google.appengine.ext import ndb
import logging

from model import Monitor, Product, User


def create_user_entity(uid, check=True):
    user = User.get_by_id(id=uid)
    if user is not None:
        return user.key
    else:
        user = User(id=uid)
        key = user.put()
        return key

def create_monitor_entity(user_id, product_id, threshold): #!!
    monitor = Monitor.query(ndb.AND(Monitor.user == user_id, Monitor.target == product_id)).get()
    if monitor is not None:
        return monitor.key
    else:
        monitor = Monitor(user=user_id, target=product_id, threshold=threshold)
        key = monitor.put()
        return key

def create_product_entity(link, current, lowest, history, meta):
    product = Product.get_by_id(id=meta["asin"])
    if product is not None:
        return product.key
    else:
        product = Product(id=meta["asin"], link=link, current=current, lowest=lowest, history=history, meta=meta)
        key = product.put()
        return key

def fetch_by_urlsafe_key(key):
        entity_key = ndb.Key(urlsafe=key)
        entity = entity_key.get()
        return entity

def has_quota(uid):
    user = User.get_by_id(id=uid)
    num_monitoring = Monitor.query(ndb.AND(Monitor.user == uid, Monitor.switch == True)).count()
    return num_monitoring < user.quota

def get_monitoring(uid):
    monitoring = Monitor.query(ndb.AND(Monitor.user == uid, Monitor.switch == True)).fetch()
    products = ndb.get_multi([m.target for m in monitoring])
    return zip(monitoring, products)
    
#def is_monitoring(uid, product_key):
#    monitoring = Monitor.query(ndb.AND(Monitor.uid == uid, ndb.AND(Monitor.target == product_key, Monitor.switch == True))).get()
#    if monitoring:
#    	return monitoring.key
#    else:
#    	return False

#def get_triggered_alert(asin, price):
#    monitoring = Monitor.query(ndb.AND(current, Monitor.switch == True, ndb.AND(Monitor.asin == asin, Monitor.threshold > current))).fetch(limit=100)
#    return monitoring
    
