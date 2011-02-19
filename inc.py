import sys, time, os
# from mingus.midi import fluidsynth
from mingus.containers import *
import OSC
import tornado.httpserver
import tornado.ioloop
import tornado.web
import inc_io
from settings import *
try:
    import json
except:
    import simplejson as json

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
    
    def increase_velocity(self):
        self.velocity = min(self.velocity + 10, 110)
        
    def decrease_velocity(self):
        self.velocity = max(self.velocity - 10, 0)
    
    def stop_note(self, note=None):
        # note param is not currently used, but would be necessary if we added support for chords
        global occam
        if self.last_note is not None:
            print "stopping note %s" % str(self.last_note)
            occam.stop_Note(self.last_note, self.channel)
            self.last_note = None            
    
    def play_note(self, note):
        print "playing note %s" % str(note)
        global occam
        occam.play_Note(note, self.channel, self.velocity)        
        self.last_note = note
        
    def __str__(self):
        return "<Player %s/%d/%d>" % (self.piece, self.channel, self.velocity)


class AdminHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("%sadmin.html" % TEMPLATE_DIR, title="In C Admin", pieces=self.pieces)
        

class Conductor(object):    
    def __init__(self):
        super(Conductor, self).__init__()

        self.tic = 0
        self.time_interval = 60.0 / (TICS_PER_MINUTE * 1.0)
        print "time interval is %f" % self.time_interval
        self.pieces = inc_io.load()
        self._build_piece_events()
        self.piece_lengths = {}
        for (i,p) in self.piece_events.items():
            self.piece_lengths[i] = len(self.piece_events[i])        

        self.players = []
        for i in range(0, NUM_PLAYERS):
            self.players.append(Player())

        global occam
        occam = Occam()


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
            (r"/", AdminHandler),
        ], **settings)

        self.http_server = tornado.httpserver.HTTPServer(self.application)
        self.http_server.listen(8888)
        # tornado.ioloop.IOLoop.instance().start()        
                
    def muster(self):
        print "Staging..."
        self.players[0].piece = '1'
        self.players[0].channel = 1
        self.players[0].offset = 0

        self.players[1].piece = '2'
        self.players[1].channel = 2
        self.players[1].offset = 0

    
    def loop(self):
        print "Starting loop..."
        # print map(lambda x: str(x), self.players)
        while True:            
            for (i,player) in enumerate(self.players):
                if player.piece is None:
                    continue
                
                # print player

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
            print self.tic 
            
            time.sleep(self.time_interval)
            
    def finish(self):
        """ Clean up lingering notes """
        for p in self.players:
            if p.last_note is not None:
                p.stop_note(p.last_note)

def main():
    conductor = Conductor()
    conductor.start_webserver()
    conductor.muster()
    
    try:
        conductor.loop()
    except:
        pass
    finally:
        conductor.finish()


def main2():
    notes = ['B-3', 'C-4', 'D-4', 'E-4', 'F-4', 'G-4', 'A-4', 'B-4', 'C-5']

    nc = NoteContainer()
    for tn in notes:
        # print tn
        n = Note(tn, 4)
        n.velocity = 100
        n.channel = 1
        nc += n

    # print nc

    for (i, note) in enumerate(nc):
        fluidsynth.play_Note(note)
        time.sleep(0.2)
        if (i%2)==0:
            # fluidsynth.stop_Note(note)
            continue

    time.sleep(2)
    
if __name__ == '__main__':
    main()