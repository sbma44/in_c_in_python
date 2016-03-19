import os.path

import logging
logger = logging.getLogger('in_c')

import tornado.httpserver, tornado.ioloop, tornado.web
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'template')

def check_messages(self, q):
    messages = []
    while not q.empty():
        try:
            messages.append(q.get(False))
        except:
            pass
    return messages

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("%sindex.html" % TEMPLATE_DIR, title="In C Admin", players=conductor.players)

class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        start_time = time.time()
        self.application.inc_q.put({'_': 'status'})

        # wait for the state update that should come back
        messages = check_messages(self.application.web_q)

        self.write(json.dumps(messages, indent=2))

        conductor.log('served result in %f seconds' % (time.time() - start_time))

class ActionHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            player_uuid = self.get_argument('player')
        except:
            return

        start_time = time.time()
        self.application.inc_q.put({'_': 'toggle', 'uuid': player_uuid })

        # wait for the state update that should come back
        state = webmonkey.web_q.get()
        while conductor.last_state_update < start_time:
            conductor.handle_messages()
            time.sleep(0.01)

        self.write(conductor.last_state_json)
        LOGGER.info('served result in %f seconds' % (time.time() - start_time))


def start(inc_q, web_q):
    logger.info('Starting webserver...')

    app = tornado.web.Application([
        (r'/', IndexHandler),
        (r'/action', ActionHandler),
        (r'/status', StatusHandler),
    ], static_path=os.path.join(os.path.dirname(__file__), 'static'))

    app.inc_q = inc_q
    app.web_q = web_q

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8001)
    tornado.ioloop.IOLoop.instance().start()