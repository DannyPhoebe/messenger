# -*- coding: utf-8 -*-

from google.appengine.ext import ndb
import logging

from model import Monitor, Product, User


def create_user_entity(uid, check=True):
    if check:
        user = User.get_by_id(id=uid)
        if user is not None:
            return user.key
    user = User(id=uid)
    key = user.put()
    return key

def create_monitor_entity(user_id, product_id, threshold, check=True):
    from datetime import datetime
    if check:
        monitor = Monitor.query(ndb.AND(Monitor.user == user_id, Monitor.target == product_id)).get()
        if monitor is not None:
            return monitor.key if (datetime.now() - monitor.timestamp).seconds > 3600 else None # block duplicate message within
    monitor = Monitor(user=user_id, target=product_id, threshold=threshold)
    key = monitor.put()
    return key

def create_product_entity(link, currency, current, history, meta):
    product = Product.get_by_id(id=meta["asin"])
    if product is not None:
        return product.key
    else:
        product = Product(id=meta["asin"], link=link, currency=currency, current=current, history=history, meta=meta)
        key = product.put()
        return key

def fetch_by_urlsafe_key(key, urlsafe=True):
    if urlsafe:
        entity_key = ndb.Key(urlsafe=key)
        entity = entity_key.get()
        return entity
    else:
        product = Product.get_by_id(id=key)
        return product

def has_quota(uid):
    user = User.get_by_id(id=uid)
    num_monitoring = Monitor.query(ndb.AND(Monitor.user == uid, Monitor.switch == True)).count()
    return num_monitoring < user.quota

def get_monitoring(uid):
    monitoring = Monitor.query(ndb.AND(Monitor.user == uid, Monitor.switch == True)).fetch()
    products = ndb.get_multi([Product.get_by_id(m.target).key for m in monitoring])
    return zip(monitoring, products)

def get_all_products(only_monitoring=True):
    if only_monitoring: # only update those are monitored
        monitoring = Monitor.query(Monitor.switch == True).fetch()
        product_ids = {_.target for _ in monitoring}
        products = [Product.get_by_id(key) for key in product_ids]
    else:
        products = Product.query().fetch()
    return products

def touch_alert(product_key):  # cron at specific time?
    #product_entity = Product.get_by_id(product_key)
    product_entity = fetch_by_urlsafe_key(product_key)
    current = product_entity.current
    asin = product_entity.key.id()
    query1 = Monitor.query(ndb.AND(Monitor.target == asin, Monitor.switch == True))
    query2 = query1.filter(Monitor.threshold >= current)
    query3 = query2.filter(Monitor.alert == False)
    touch_alert_list = query3.fetch()
    #touch_alert_list = Monitor.query(
    #    ndb.AND(Monitor.target == asin,
    #        ndb.AND(Monitor.threshold > current,
    #            ndb.AND(Monitor.switch == True,
    #                Monitor.alert == False)))).fetch()
    return touch_alert_list

#    products = ndb.get_multi([Product.get_by_id(m.target).key for m in monitoring])
#    return zip(monitoring, products)
    
#def is_monitoring(uid, product_key):
#    monitoring = Monitor.query(ndb.AND(Monitor.uid == uid, ndb.AND(Monitor.target == product_key, Monitor.switch == True))).get()
#    if monitoring:
#    	return monitoring.key
#    else:
#    	return False

#def get_triggered_alert(asin, price):
#    monitoring = Monitor.query(ndb.AND(current, Monitor.switch == True, ndb.AND(Monitor.asin == asin, Monitor.threshold > current))).fetch(limit=100)
#    return monitoring
    
