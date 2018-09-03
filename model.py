# -*- coding: utf-8 -*-

from google.appengine.ext import ndb

class User(ndb.Model):
    quota = ndb.IntegerProperty(indexed=True, default=3)

class Product(ndb.Model): # asin as key
    link = ndb.StringProperty(indexed=False)
    lowest = ndb.FloatProperty(indexed=False, default=None)
    current = ndb.FloatProperty(indexed=False, default=None)
    meta = ndb.JsonProperty(indexed=False)
    history = ndb.JsonProperty(indexed=False)
    timestamp = ndb.DateTimeProperty(auto_now=True)
    #    symbol = ndb.StringProperty(indexed=True)

class Monitor(ndb.Model):
    #user = ndb.StructuredProperty(User, indexed=True)
    user = ndb.StringProperty(indexed=True)
    target = ndb.StringProperty(indexed=True) 
    #target = ndb.StructuredProperty(Product, indexed=True)
    switch = ndb.BooleanProperty(indexed=True, default=False)
    threshold = ndb.FloatProperty(indexed=False)
    #alert = ndb.ComputedProperty(lambda self: self.threshold < self.target.current)  # !!!
    #alert = ndb.BooleanProperty(indexed=True, default=False)
    timestamp = ndb.DateTimeProperty(auto_now=True)
