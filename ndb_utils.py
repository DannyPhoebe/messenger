# -*- coding: utf-8 -*-

from google.appengine.ext import ndb

from model import Monitor, Product
import logging

MONITOR_QUOTA = 3

def create_monitor_entity(uid, product_key, threshold):
    monitor = Monitor.query(ndb.AND(Monitor.uid == uid, Monitor.target == product_key)).get()
    if monitor is not None:
        return monitor.key
    else:
        monitor = Monitor(uid=uid, target=product_key, threshold=threshold)
        monitor_key = monitor.put()
    return monitor_key

def create_product_entity(link, highest, lowest, current, meta):
    product = Product.get_by_id(id=meta["asin"])
    if product is not None:
        return product.key
    else:
        product = Product(id=meta["asin"], link=link, highest=highest, lowest=lowest, current=current, meta=meta)
        product_key = product.put()
        return product_key

def fetch_by_key(key):
        entity_key = ndb.Key(urlsafe=key)
        entity = entity_key.get()
        return entity

def monitor_quota(uid, limit=MONITOR_QUOTA):
    num_used = Monitor.query(ndb.AND(Monitor.uid == uid, Monitor.switch == True)).count()
    logging.info(num_used)
    return num_used < limit

def is_monitoring(uid, product_key):
    monitoring = Monitor.query(ndb.AND(Monitor.uid == uid, ndb.AND(Monitor.target == product_key, Monitor.switch == True))).get()
    if monitoring:
    	return monitoring.key
    else:
    	return False

def get_monitoring(uid):
    monitoring = Monitor.query(ndb.AND(Monitor.uid == uid, Monitor.switch == True)).fetch(limit=MONITOR_QUOTA)
    return monitoring

#def create_query_entity(uid, asin):
#        query = Query.get_by_id(id=uid)
#        product = Product.get_by_id(id=asin)
#        monitor_key = created_monitor_entity(product.)
#        if query is not None:
#            query.collection.append(monitor_key.get())
#            query_key = query.put()
#            return query_key.urlsafe(), monitor_key.urlsafe()
#        else:
#            query = Query(id=uid, collection=[monitor_key.get()])
#            query_key = query.put()
#            return query_key.urlsafe(), monitor_key.urlsafe()

