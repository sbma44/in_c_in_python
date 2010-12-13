import sys, time
from mingus.midi import fluidsynth
from mingus.containers import *
import tornado.httpserver
import tornado.ioloop
import tornado.web
import inc_io
from settings import *
try:
    import json
except:
    import simplejson as json

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


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")
        

class Conductor(object):    
    def __init__(self):
        super(Conductor, self).__init__()

        self.global_offset = 0

        self.pieces = inc_io.load()
        self._build_piece_events()

        self.players = [ Player() ] * NUM_PLAYERS

        fluidsynth.init(SOUNDFONT_FILE)


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
        self.application = tornado.web.Application([
            (r"/", MainHandler),
        ])

        self.http_server = tornado.httpserver.HTTPServer(self.application)
        self.http_server.listen(8888)
        tornado.ioloop.IOLoop.instance().start()
                
    def muster(self):
        pass            
    
    def loop(self):
        while True:
            time.sleep(1)


def main():
    conductor = Conductor()
    conductor.start_webserver()
    conductor.muster()
    conductor.loop()


def main2():
    notes = ['B-3', 'C-4', 'D-4', 'E-4', 'F-4', 'G-4', 'A-4', 'B-4', 'C-5']

    nc = NoteContainer()
    for tn in notes:
        print tn
        n = Note(tn, 4)
        n.velocity = 100
        n.channel = 1
        nc += n

    print nc

    for (i, note) in enumerate(nc):
        fluidsynth.play_Note(note)
        time.sleep(0.2)
        if (i%2)==0:
            # fluidsynth.stop_Note(note)
            continue

    time.sleep(2)
    
if __name__ == '__main__':
    main()