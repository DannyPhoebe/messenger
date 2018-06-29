# -*- coding: utf-8 -*-

from google.appengine.ext import ndb

class Product(ndb.Model): # asin as key
    link = ndb.StringProperty(indexed=False)
    highest = ndb.IntegerProperty(indexed=False)
    lowest = ndb.IntegerProperty(indexed=False)
    current = ndb.JsonProperty(indexed=False)
    meta = ndb.JsonProperty(indexed=False)
    timestamp = ndb.DateTimeProperty(auto_now=True)

class Monitor(ndb.Model):
    uid = ndb.StringProperty(indexed=True) 
    target = ndb.StructuredProperty(Product)
    switch = ndb.BooleanProperty(indexed=True, default=False)
    threshold = ndb.IntegerProperty(indexed=False)
    alert = ndb.ComputedProperty(lambda self: self.target.current[-1][0] < self.threshold)
    timestamp = ndb.DateTimeProperty(auto_now=True)

#class Query(ndb.Model):
#    collection = ndb.StructuredProperty(Monitor, repeated=True)
#    timestamp = ndb.DateTimeProperty(auto_now=True)

