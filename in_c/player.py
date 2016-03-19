try:
    import json
except Exception, e:
    import simplejson as json


class Player(object):    
    def __init__(self, conductor, piece=None, offset=0, octave_shift=0, instrument=None, channel=None):
        self.name = ''
        self.key = -1
        self.conductor = conductor
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
        if self.last_note is not None:
            # print "stopping note %s" % str(self.last_note)
            self.conductor.occam.stop_Note(self.last_note, self.channel)
            self.last_note = None            
    
    def play_note(self, note):
        # print "playing note %s" % str(note)
        self.conductor.occam.play_Note(note, self.channel, self.velocity)        
        self.last_note = note
        
    def __str__(self):
        return "<Player %s/%d/%d>" % (self.piece, self.channel, self.velocity)
        
    def to_dict(self):
        return {'piece': self.piece, 'offset': self.offset, 'octave_shift': self.octave_shift, 'instrument': self.instrument, 'channel': self.channel, 'velocity': self.velocity, 'mute': self.mute}

    def from_dict(self, data):
        self.piece = str(data['piece'])
        self.offset = int(data['offset'])
        self.octave_shift = int(data['octave_shift'])
        self.instrument = data['instrument']
        self.channel = data['channel'] is not None and int(data['channel']) or None
        self.velocity = int(data['velocity'])
        self.mute = data['mute']