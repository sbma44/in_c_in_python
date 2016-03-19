import json
from in_c.settings import *

class NoteEvent(object):
    def __init__(self, name='C', octave=4, dynamics={}, duration=1, is_rest=False):
        if not is_rest:
            self.name = name
            self.octave = octave
            self.dynamics = dynamics
            self.midi = MIDI_LOOKUP.get('%s%d' % (self.name, self.octave))
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
            return "%s%d/%d" % (self.name, self.octave, self.duration)

def build(pieces):
        # play event example (note: not actual piece data)
        # { 1: [    [ (False = Note Off|True= Note On, Note) ]    ] }
        # { 2: [ [(True, "C#")], [], [], [(False, "C#"), (True, "D")], [], [(False, "D")] ] }

        # construct a list to hold the events that must occur at
        # each tic of each piece
        piece_events = [ [] for x in pieces ]
        for (i, piece) in enumerate(pieces):
            for note_event in piece:
                if note_event.is_rest:
                    piece_events[i].append(None)
                else:
                    piece_events[i].append([ note_event ])

                # pad out duration
                for x in range(0, note_event.duration - 1):
                    piece_events[i].append(None)

        return piece_events

def generate_json(out_file=None):
    complete_piece = {}
    for i in range(1, 54):

        complete_piece[i] = []

        with open(os.path.join(INC_PIECE_DIR, '{}.txt'.format(i))) as f:
            lines = [ line for line in f.readlines() if line.strip()[0] != '#' and len(line.strip()) > 0 ]

        for l in lines:
            (tone, duration) = [ x.strip().upper() for x in l.split(',') ]
            if tone == 'R':
                note = NoteEvent(is_rest=True, duration=int(duration))
            else:
                (name, octave) = tone.split('-')
                note = NoteEvent(name=name, octave=int(octave), duration=duration, dynamics={}, is_rest=False)

            complete_piece[i].append(note.to_tuple())

    if out_file is None:
        return json.dumps(complete_piece, indent=2)
    else:
        json.dump(complete_piece, out_file, indent=2)

def load():
    j = []
    with open(INC_SOURCE) as f:
        for (i, note_events) in sorted(json.load(f).items(), key=lambda x: int(x[0])):
            j.append( [ NoteEvent.from_tuple(x) for x in note_events ] )
    return j

MIDI_LOOKUP = {"C0" : 0, "C#0" : 1, "D0" : 2,
        "D#0" : 3, "E0" : 4, "F0" : 5,
        "F#0" : 6, "G0" : 7, "G#0" : 8,
        "A0" : 9, "A#0" : 10, "B0" : 11,
        "C1" : 12, "C#1" : 13, "D1" : 14,
        "D#1" : 15, "E1" : 16, "F1" : 17,
        "F#1" : 18, "G1" : 19, "G#1" : 20,
        "A1" : 21, "A#1" : 22, "B1" : 23,
        "C2" : 24, "C#2": 25, "D2" : 26,
        "D#2" : 27, "E2" : 28, "F2" : 29,
        "F#2" : 30, "G2" : 31, "G#2" : 32,
        "A2" : 33, "A#2" : 34, "B2" : 35,
        "C3" : 36, "C#3" : 37, "D3" : 38,
        "D#3" : 39, "E3" : 40, "F3" : 41,
        "F#3" : 42, "G3" : 43, "G#3" : 44,
        "A3" : 45, "A#3" : 46, "B3" : 47,
        "C4" : 48, "C#4" : 49, "D4" : 50,
        "D#4" : 51, "E4" : 52, "F4" : 53,
        "F#4" : 54, "G4" : 55, "G#4" : 56,
        "A4" : 57, "A#4" : 58, "B4" : 59,
        "C5" : 60, "C#5" : 61, "D5" : 62,
        "D#5" : 63, "E5" : 64, "F5" : 65,
        "F#5" : 66, "G5" : 67, "G#5" : 68,
        "A5" : 69, "A#5" : 70, "B5" : 71,
        "C6" : 72, "C#6" : 73, "D6" : 74,
        "D#6" : 75, "E6" : 76, "F6" : 77,
        "F#6" : 78, "G6" : 79, "G#6" : 80,
        "A6" : 81, "A#6" : 82, "B6" : 83,
        "C7" : 84, "C#7" : 85, "D7" : 86,
        "D#7" : 87, "E7" : 88, "F7" : 89,
        "F#7" : 90, "G7" : 91, "G#7" : 92,
        "A7" : 93, "A#7" : 94, "B7" : 95,
        "C8" : 96, "C#8" : 97, "D8" : 98,
        "D#8" : 99, "E8" : 100, "F8" : 101,
        "F#8" : 102, "G8" : 103, "G#8" : 104,
        "A8" : 105, "A#8" : 106, "B8" : 107,
        "C9" : 108, "C#9" : 109, "D9" : 110,
        "D#9" : 111, "E9" : 112, "F9" : 113,
        "F#9" : 114, "G9" : 115, "G#9" : 116,
        "A9" : 117, "A#9" : 118, "B9" : 119,
        "C10" : 120, "C#10" : 121, "D10" : 122,
        "D#10" : 123, "E10" : 124, "F10" : 125,
        "F#10" : 126, "G10" : 127}

if __name__ == '__main__':
    with open(JSON_FILENAME, 'w') as f:
        generate_json(f)
