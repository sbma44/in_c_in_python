import tornado.httpserver, tornado.ioloop, tornado.web
import os
from settings import *

class AdminHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("%sadmin.html" % TEMPLATE_DIR, title="In C Admin", pieces=['a', 'b', 'c'])


def main():
    print "Starting webserver..."
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), "web", "static"),
    }
    application = tornado.web.Application([
        (r"/", AdminHandler),
    ], **settings)
    
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
        
    
if __name__ == '__main__':
    main()