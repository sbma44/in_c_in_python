import inc
from mingus.containers import *
try:
    import json
except Exception, e:
    import simplejson as json
from settings import *

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

def generate_json(out_file=None):
    complete_piece = {}
    for i in range(1, 54):
    
        complete_piece[i] = []
    
        f = open('%s%d.txt' % (INC_SRC,i), 'r')
        lines = f.readlines()
        f.close()
        for l in lines:
            if l[0]=='#' or len(l.strip())==0:
                continue
        
            (tone, duration) = l.split(',')
            if tone.upper().strip()=='R':
                note = NoteEvent(is_rest=True, duration=int(duration))
            else:
                (name, octave) = tone.split('-')
                note = NoteEvent(name=name, octave=int(octave), duration=duration, dynamics={}, is_rest=False)
    
            complete_piece[i].append(note.to_tuple())

    if f is None:
        return json.dumps(complete_piece)
    else:
        json.dump(complete_piece, out_file)

def load():
    f = open(JSON_FILENAME)
    j = json.load(f)
    for (i, note_events) in j.items():
        j[i] = map(lambda x: NoteEvent.from_tuple(x), note_events)        
    return j

if __name__ == '__main__':
    f = open(JSON_FILENAME, 'w')
    generate_json(f)
    f.close()
    