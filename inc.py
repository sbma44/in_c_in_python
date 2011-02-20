import sys, time, os, signal, fcntl
import tornado.httpserver, tornado.ioloop, tornado.web
from mingus.containers import *
import OSC
import music_loader as inc_io
import ui
from settings import *

conductor = None

def dblog(msg):
    f = open('error.txt','a')
    f.write("%s\n" % msg)
    f.close()

class Occam(object):
    """ OSC/MIDI Bridge """
    def __init__(self):
        super(Occam, self).__init__()
        self.client = OSC.OSCClient()
        self.client.connect( OCCAM_SERVERS[0] )

        self.note_on = OSC.OSCMessage()
        self.note_on.setAddress("/osc/midi/out/noteOn")

        self.note_off = OSC.OSCMessage()
        self.note_off.setAddress("/osc/midi/out/noteOff")
        
    def play_Note(self, note, channel, velocity):
        self.note_on.clearData()
        self.note_on.append(channel)
        self.note_on.append(int(note))
        self.note_on.append(velocity)
        self.client.send(self.note_on)
        
    def stop_Note(self, note, channel):
        self.note_off.clearData()
        self.note_off.append(channel)
        self.note_off.append(int(note))
        self.note_off.append(120)
        self.client.send(self.note_off)


class NoteEvent(Note):
    def __init__(self, name='C', octave=4, dynamics={}, duration=1, is_rest=False):
        if not is_rest:
            Note.__init__(self, str(name), int(octave), dynamics) # old-style call due to Mingus not using new-style inheritance (ugh)
        self.is_rest = is_rest
        self.duration = int(duration)        
        
    def to_tuple(self):
        return (self.name, self.octave, self.dynamics, self.duration, self.is_rest)
    
    @staticmethod
    def from_tuple(t):
        return NoteEvent(name=t[0], octave=t[1], dynamics=t[2], duration=t[3], is_rest=t[4])
        
    def __repr__(self):
        if self.is_rest:
            return "REST/%d" % self.duration
        else:
            return "%s/%d" % (Note.__repr__(self), self.duration)

class Player(object):    
    def __init__(self, piece=None, offset=0, octave_shift=0, instrument=None, channel=None):
        self.piece = piece
        self.offset = offset
        self.octave_shift = octave_shift
        self.instrument = instrument
        self.channel = channel
        self.velocity = 70
        self.last_note = None
        self.mute = False
    
    def increase_velocity(self):
        self.velocity = min(self.velocity + 10, 110)
        
    def decrease_velocity(self):
        self.velocity = max(self.velocity - 10, 0)
    
    def stop_note(self, note=None):
        # note param is not currently used, but would be necessary if we added support for chords
        # global conductor
        if self.last_note is not None:
            # print "stopping note %s" % str(self.last_note)
            conductor.occam.stop_Note(self.last_note, self.channel)
            self.last_note = None            
    
    def play_note(self, note):
        # print "playing note %s" % str(note)
        # global conductor
        conductor.occam.play_Note(note, self.channel, self.velocity)        
        self.last_note = note
        
    def __str__(self):
        return "<Player %s/%d/%d>" % (self.piece, self.channel, self.velocity)



class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("%sadmin.html" % TEMPLATE_DIR, title="In C Admin", players=conductor.players)

class ActionHandler(tornado.web.RequestHandler):
    def get(self):    
        dblog('serving request')            
        try:
            player_id = int(self.get_argument('player'))
        except:
            return

        global conductor
        
        if player_id<0 or player_id>=len(conductor.players):
            return
        
        conductor.send_message('toggle/%d' % player_id)
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
        self._spare_buffer = ['', '']

        # initialize player objects
        self.players = []
        for i in range(0, NUM_PLAYERS):
            self.players.append(Player())

        # create MIDI bridge
        self.occam = Occam()


    def send_message(self, msg):  
        dblog('sending %s' % msg)
        try:      
            socket = self.webserver_pid==0 and self.web_tx or self.inc_tx
            os.write(socket, "%s#\n" % msg.strip())
        except Exception, e:
            dblog(str(e))
        dblog('sent')

        
    def check_messages(self):
        if self.webserver_pid!=0:
            socket = self.web_rx
            buf_i = 0
        else:    
            socket = self.inc_rx
            buf_i = 1
        
        data = None
        try:
            data = os.read(socket, 1024)
        except Exception, e:
            return []
                
        if len(self._spare_buffer):
            data = "%s%s" % (self._spare_buffer[buf_i], data)
            self._spare_buffer[buf_i] = ''
            
        messages = data.split("\n")

        if messages[-1]=='':
            del messages[-1]

        if len(messages[-1])>0 and messages[-1][-1]!='#':
            self._spare_buffer = t
            del messages[-1]
            
        messages = map(lambda x: x[:-1], messages)

        return messages

            
    def toggle_player(self, i):
        if type(i) is not int:
            return
        if i<0 or i>=len(self.players):
            return
            
        global conductor
        conductor.players[i].mute = not conductor.players[i].mute
        if conductor.players[i].last_note is not None:
            conductor.players[i].stop_note(conductor.players[i].last_note)

        print "player %d muted: %s" % (i, str(conductor.players[i].mute))

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
            args = m.split('/')
            if args[0]=='toggle':
                try:
                    player_id = int(args[1])
                except:
                    return
                self.toggle_player(player_id)
    
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