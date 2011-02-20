import sys, time, os, signal, fcntl
import tornado.httpserver, tornado.ioloop, tornado.web
import OSC
from occam import Occam
import music_loader as inc_io
from player import Player
import ui
try:
    import json
except Exception, e:
    import simplejson as json
from settings import *


conductor = None

class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("%sadmin.html" % TEMPLATE_DIR, title="In C Admin", players=conductor.players)

class ActionHandler(tornado.web.RequestHandler):
    def get(self):    
        conductor.dblog('serving request')            
        try:
            player_id = int(self.get_argument('player'))
        except:
            return

        if player_id<0 or player_id>=len(conductor.players):
            return

        conductor.send_message({'_': 'toggle', 'player': player_id })
        self.write('1')

class Conductor(object):    
    def __init__(self):
        super(Conductor, self).__init__()

        # set performance constants
        self.tic = 0
        self.time_interval = 60.0 / (TICS_PER_MINUTE * 1.0)

        # load music
        self.pieces = inc_io.load()
        self._build_piece_events()
        self.piece_lengths = {}
        for (i,p) in self.piece_events.items():
            self.piece_lengths[i] = len(self.piece_events[i])        

        # interprocess stuff
        self.webserver_pid = None
        self.web_rx, self.web_tx = os.pipe()
        self.inc_rx, self.inc_tx = os.pipe()
        # set pipes to not block
        fcntl.fcntl(self.web_rx, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.web_tx, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.inc_rx, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.inc_tx, fcntl.F_SETFL, os.O_NONBLOCK)

        # initialize player objects
        self.players = []
        for i in range(0, NUM_PLAYERS):
            self.players.append(Player(conductor=self))

        # create MIDI bridge
        self.occam = Occam()

    def dblog(msg):
        conductor.send_message({'_':'log','message':msg})


    def send_message(self, msg):  
        assert type(msg) is dict

        try:      
            socket = self.webserver_pid==0 and self.web_tx or self.inc_tx

            msg['time'] = time.time()
            encoded_msg = json.dumps(msg)
            if len(encoded_msg)>MAX_MESSAGE_SIZE:
                self.dblog('Error: JSON package too large.')
            else:
                os.write(socket, "%s\n" % encoded_msg)
        except Exception, e:
            self.dblog(str(e))


    def check_messages(self):
        if self.webserver_pid!=0:
            socket = self.web_rx
            buf_i = 0
        else:    
            socket = self.inc_rx
            buf_i = 1

        data = ''
        buffer_empty = False
        while not buffer_empty:
            try:
                data = data + os.read(socket, MAX_MESSAGE_SIZE)
            except Exception, e:
                buffer_empty = True

        if len(data)==0:
            return []

        messages = data.split("\n")

        if len(messages[-1])==0:
            del messages[-1]

        decoded_messages = []
        for m in messages:
            try:
                decoded_messages.append(json.loads(m))
            except:
                decoded_messages.append({'_': 'decode_failure', 'data': m})

        return decoded_messages


    def toggle_player(self, i):
        if type(i) is not int:
            return
        if i<0 or i>=len(self.players):
            return

        self.conductor.players[i].mute = not self.conductor.players[i].mute
        if self.conductor.players[i].last_note is not None:
            self.conductor.players[i].stop_note(self.conductor.players[i].last_note)

        print "player %d muted: %s" % (i, str(self.conductor.players[i].mute))

    def _build_piece_events(self):
        # play event example (note: not actual piece data)
        # { 1: [    [ (False = Note Off|True= Note On, Note) ]    ] }
        # { 2: [ [(True, "C#")], [], [], [(False, "C#"), (True, "D")], [], [(False, "D")] ] }
        self.piece_events = {}

        currently_playing = {}
        for e in self.pieces:
            currently_playing[e] = False

        for (i,piece) in self.pieces.items():

            # construct a list to hold the events that must occur at each tic of this piece
            self.piece_events[i] = []

            for note_event in piece:

                # place rest
                if note_event.is_rest:

                    if currently_playing[i] is False:
                        # nothing was just playing -- we don't need to turn off the previous note
                        self.piece_events[i].append( [] )
                    else:
                        # turn off the last note
                        self.piece_events[i].append( [(False, currently_playing[i])] )

                    # pad out the duration of the rest
                    for x in range(0, note_event.duration-1):
                        self.piece_events[i].append([])

                    # mark the fact that no note needs to be turned off at the next note
                    currently_playing[i] = False

                # place note
                else:
                    if currently_playing[i] is False:
                        # nothing was just playing -- we don't need to turn off the previous note
                        self.piece_events[i].append( [(True, note_event)] )
                    else:
                        # turn off the last note and start the new one
                        self.piece_events[i].append( [(False, currently_playing[i]), (True, note_event)] )

                    # pad out the duration of the note
                    for x in range(0, note_event.duration-1):
                        self.piece_events[i].append( [] )

                    # mark the note we've started playing
                    currently_playing[i] = note_event


    def start_webserver(self):
        print "Starting webserver..."
        settings = {
            "static_path": os.path.join(os.path.dirname(__file__), "web", "static"),
        }
        self.application = tornado.web.Application([
            (r'/', IndexHandler),
            (r'/action', ActionHandler)
        ], **settings)

        self.webserver_pid = os.fork()
        if self.webserver_pid==0: # in child process
            self.http_server = tornado.httpserver.HTTPServer(self.application)
            self.http_server.listen(8888)
            tornado.ioloop.IOLoop.instance().start()


    def muster(self):
        for i in range(1, 6):
            self.players[i].piece = str(i)
            self.players[i].channel = i
            self.players[i].offset = 0


    def deal_with_input(self):
        msgs = self.check_messages()
        for m in msgs:
            if m['_']=='toggle':
                try:
                    player_id = int(m['player'])
                except:
                    return
                self.toggle_player(player_id)
            elif m['_']=='decode_failure':
                print "Failed to decode JSON message: %s" % m['data']
            elif m['_']=='log':
                print "LOG: %s" % m['message']

    def loop(self):
        print "Starting loop..."
        while True:            
            for (i,player) in enumerate(self.players):
                if player.piece is None or player.mute:
                    continue

                events = self.piece_events[player.piece][(self.tic + player.offset) % self.piece_lengths[player.piece]]
                if len(events)==0:
                    continue
                else:
                    # print events
                    for (note_on, note) in events:                            
                        if note_on:
                            player.play_note(note)
                        else:
                            player.stop_note(note)

            time.sleep(self.time_interval)    
            self.tic += 1           
            # print self.tic 

            self.deal_with_input()

            time.sleep(self.time_interval)

    def finish(self):
        """ Clean up lingering notes and processes """

        # get rid of the webserver zombie process
        os.kill(self.webserver_pid, signal.SIGTERM) 

        # silence lingering notes
        for p in self.players:
            if p.last_note is not None:
                p.stop_note(p.last_note)

def main():
    global conductor
    conductor = Conductor()
    conductor.start_webserver()
    conductor.muster()
    
    try:
        conductor.loop()
    except Exception, e:
        raise e
    finally:
        conductor.finish()


if __name__ == '__main__':
    main()