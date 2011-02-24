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
        self.render("%sindex.html" % TEMPLATE_DIR, title="In C Admin", players=conductor.players)

class StatusHandler(tornado.web.RequestHandler):
    def get(self):
        start_time = time.time()
        conductor.send_message({'_': 'status'})

        # wait for the state update that should come back
        while conductor.last_state_update<start_time:
            conductor.handle_messages()
            time.sleep(0.01)
        
        self.write(conductor.last_state_json)
        conductor.log('served result in %f seconds' % (time.time() - start_time))

class ActionHandler(tornado.web.RequestHandler):
    def get(self):    
        try:
            player_id = int(self.get_argument('player'))
        except:
            return

        if player_id<0 or player_id>=len(conductor.players):
            return

        start_time = time.time()
        conductor.send_message({'_': 'toggle', 'player': player_id })

        # wait for the state update that should come back
        while conductor.last_state_update<start_time:
            conductor.handle_messages()
            time.sleep(0.01)
        
        self.write(conductor.last_state_json)
        conductor.log('served result in %f seconds' % (time.time() - start_time))


class NoteHospice(object):
    """ They will receive the very best of care, but these notes are dying """
    def __init__(self):
        super(NoteHospice, self).__init__()
        self.notes = []
    
    def add(self, player, note):
        self.notes.append( [note, player, note.duration] )
    
    def still_playing(self):
        return len(self.notes)>0
    
    def cycle(self):
        to_delete = []
        for i in range(0, len(self.notes)):
            # decrement duration            
            self.notes[i][2] = self.notes[i][2] - 1

            # stop a note if it's at zero
            if self.notes[i][2]<=0:
                self.notes[i][1].stop_note(self.notes[i][0])
                to_delete.append(i)
                
        for i in reversed(sorted(to_delete)):
            self.notes.pop(i)
    

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
        self.note_hospice = NoteHospice()       

        # interprocess stuff
        self.webserver_pid = None
        self.is_webserver_process = False
        self.web_rx, self.web_tx = os.pipe()
        self.inc_rx, self.inc_tx = os.pipe()
        # set pipes to not block
        fcntl.fcntl(self.web_rx, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.web_tx, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.inc_rx, fcntl.F_SETFL, os.O_NONBLOCK)
        fcntl.fcntl(self.inc_tx, fcntl.F_SETFL, os.O_NONBLOCK)
        self.last_state_update = 0
        self.last_state_json = ''

        # initialize player objects
        self.players = []
        for i in range(0, NUM_PLAYERS):
            self.players.append(Player(conductor=self))

        # create MIDI bridge
        self.occam = Occam()


    def toggle_player(self, i):
        if type(i) is not int:
            return
        if i<0 or i>=len(self.players):
            return

        self.players[i].mute = not self.players[i].mute
        if self.players[i].mute and self.players[i].last_note is not None:
            self.players[i].stop_note(self.players[i].last_note)

        # print "player %d muted: %s" % (i, str(self.players[i].mute))

        
    def _print_log_message(self, msg):
        print "LOG: %s" % msg
        
    def log(self, msg):
        if self.is_webserver_process:
            self.send_message({'_':'log','message':msg})
        else:
            self._print_log_message(msg)

    def send_message(self, msg):  
        assert type(msg) is dict

        try:      
            socket = self.is_webserver_process and self.web_tx or self.inc_tx

            msg['_t'] = time.time()
            encoded_msg = json.dumps(msg)
            if len(encoded_msg)>MAX_MESSAGE_SIZE:
                self.log('Error: JSON package too large.')
            else:
                os.write(socket, "%s\n" % encoded_msg)
        except Exception, e:
            self.log(str(e))


    def check_messages(self):
        if not self.is_webserver_process:
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
                decoded_messages.append((json.loads(m), m))
            except:
                decoded_messages.append(({'_': 'decode_failure'}, m))

        return decoded_messages
        
    def send_state(self):
        message = { '_': 'state_xfer', 'player_keys': [], 'players': {} }
        for (i,p) in enumerate(self.players):
            self.players[i].key = i # ensure that player objects know how to refer to themselves when speaking to the conductor
            message['players'][p.name] = p.to_dict()
            message['player_keys'].append(p.key)
        self.send_message(message)

    def _build_piece_events(self):
        # play event example (note: not actual piece data)
        # { 1: [    [ (False = Note Off|True= Note On, Note) ]    ] }
        # { 2: [ [(True, "C#")], [], [], [(False, "C#"), (True, "D")], [], [(False, "D")] ] }
        #
        # NOTE: "note off" events are deprecated; a superior but slightly more computationally demanding note-expiration
        # mechanism. Using the "player piano roll" approach created here led to some non-expiring notes, and I didn't
        # feel like tracking down what was sure to be a hellacious bug
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
            (r'/action', ActionHandler),
            (r'/status', StatusHandler),
        ], **settings)

        self.webserver_pid = os.fork()
        if self.webserver_pid==0: # in child process
            self.is_webserver_process = True
            self.http_server = tornado.httpserver.HTTPServer(self.application)
            self.http_server.listen(8888)
            tornado.ioloop.IOLoop.instance().start()


    def create_dummy_players(self):
        for i in range(0, NUM_PLAYERS):
            self.players[i].piece = str(i+1)
            self.players[i].channel = i+1
            self.players[i].offset = 0

        for (i,p) in enumerate(self.players):
            self.players[i].name = i
            
    def muster(self):
        pass


    def handle_messages(self):
        msgs = self.check_messages()
        for (m, src) in msgs:
            action = m['_']

            if action=='toggle':
                try:
                    player_id = int(m['player'])
                except:
                    continue
                self.toggle_player(player_id)
                self.send_state()

            elif action=='state_xfer':
                for (i,p) in m['players'].items():
                    self.players[int(i)].from_dict(p)
                self.last_state_update = m['_t']     
                self.last_state_json = src
            
            elif action=='status':
                self.send_state()

            elif action=='decode_failure':
                print "Failed to decode JSON message: %s" % src

            elif action=='log':
                self._print_log_message(m['message'])


    def loop(self):
        print "Starting loop..."
        while True:            
            
            start = time.time()
            
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
                            self.note_hospice.add(player, note)

            end = time.time()

            time.sleep(self.time_interval - (end-start))    

            # kill notes that need to be killed
            self.note_hospice.cycle()

            self.tic += 1           

            self.handle_messages()

            time.sleep(self.time_interval)

    def finish(self):
        """ Clean up lingering notes and processes """

        # get rid of the webserver zombie process
        os.kill(self.webserver_pid, signal.SIGTERM) 

        # silence lingering notes
        while self.note_hospice.still_playing():
            self.note_hospice.cycle()

        # for p in self.players:
        #     if p.last_note is not None:
        #         p.stop_note(p.last_note)

def main():
    global conductor
    conductor = Conductor()
    conductor.create_dummy_players()
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