#-*- coding: UTF-8 -*-
#/usr/bin/env python

# [START app]
import webapp2

class StartHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write("Warmup successful")

config = {}
app = webapp2.WSGIApplication([
    ('/_ah/start', StartHandler),
], config=config)  # debug=True

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=80, debug=True)

# [END app]
