# -*- coding: utf-8 -*-

from google.appengine.ext import ndb

from model import Monitor, Product

def create_monitor_entity(uid, product):
        monitor = Monitor(uid=uid, target=product, threshold=product.current[-1][0])
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

