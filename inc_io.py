import inc
from settings import *
try:
    import json
except Exception, e:
    import simplejson as json

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
                note = inc.NoteEvent(is_rest=True, duration=int(duration))
            else:
                (name, octave) = tone.split('-')
                note = inc.NoteEvent(name=name, octave=int(octave), duration=duration, dynamics={}, is_rest=False)
    
            complete_piece[i].append(note.to_tuple())

    if f is None:
        return json.dumps(complete_piece)
    else:
        json.dump(complete_piece, out_file)

def load():
    f = open(JSON_FILENAME)
    j = json.load(f)
    for (i, note_events) in j.items():
        j[i] = map(lambda x: inc.NoteEvent.from_tuple(x), note_events)        
    return j

if __name__ == '__main__':
    f = open(JSON_FILENAME, 'w')
    generate_json(f)
    f.close()
    