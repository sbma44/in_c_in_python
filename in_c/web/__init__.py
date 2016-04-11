import time
import json
import os.path

import logging
logger = logging.getLogger('in_c')

import tornado.httpserver, tornado.ioloop, tornado.web
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'template')

from in_c.settings import *

def check_messages(q):
    messages = []
    while not q.empty():
        try:
            messages.append(q.get(False))
        except:
            pass
    return messages

def wait_for_status(q):
    while True:
        resp = [m for m in check_messages(q) if m['_'] == 'state_xfer']
        if len(resp) > 0:
            return resp[-1]

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("%sindex.html" % TEMPLATE_DIR, title="In C Admin", players=conductor.players)

class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        start_time = time.time()

        self.set_header("Content-Type", 'application/json; charset="utf-8"')
        self.set_header("Access-Control-Allow-Origin", "http://127.0.0.1:8080")

        if (time.time() - self.application.in_c_status['checked']) > TIC_DURATION:
            self.application.in_c_status['checked'] = time.time()
            self.application.inc_q.put({'_': 'status'})
            state = wait_for_status(self.application.web_q)
            self.application.in_c_status['state'] = state

        self.write(json.dumps(self.application.in_c_status['state'], indent=2))

        logger.info('served result in %f seconds' % (time.time() - start_time))

class ActionHandler(tornado.web.RequestHandler):
    def get(self):
        try:
            player_uuid = self.get_argument('player')
        except:
            return

        start_time = time.time()
        self.application.inc_q.put({'_': 'toggle', 'uuid': player_uuid })

        # wait for the state update that should come back
        state = self.application.web_q.get()
        while conductor.last_state_update < start_time:
            conductor.handle_messages()
            time.sleep(0.01)

        self.write(conductor.last_state_json)
        logger.info('served result in %f seconds' % (time.time() - start_time))


def start(inc_q, web_q):
    logger.info('Starting webserver...')

    app = tornado.web.Application([
        (r'/', IndexHandler),
        (r'/action', ActionHandler),
        (r'/status', StatusHandler),
    ], static_path=os.path.join(os.path.dirname(__file__), 'static'))

    app.inc_q = inc_q
    app.web_q = web_q
    app.in_c_status = { 'checked': 0, 'state': None }

    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(8001)
    tornado.ioloop.IOLoop.instance().start()