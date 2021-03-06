import json
import uuid
from collections import defaultdict

from in_c.settings import TIC_DURATION

import logging
logger = logging.getLogger('in_c')
logger.setLevel(logging.DEBUG)

class Player(object):
    def __init__(self, conductor, name='', piece=None, offset=0, octave_shift=0, instrument=None, channel=None):
        self.name = name
        self.uuid = uuid.uuid4().hex
        self.velocity = 70
        self.muted = False

        self.conductor = conductor
        self.piece = piece
        self.offset = offset
        self.octave_shift = octave_shift
        self.instrument = instrument
        self.channel = channel

        self.simultaneous_play_count = defaultdict(int)
        self.timers = {}

    def __hash__(self):
        return self.uuid.int

    def __str__(self):
        return "<Player %s/%d/%d>" % (self.piece, self.channel, self.velocity)

    def __getstate__(self):
        return {
            'uuid': self.uuid,
            'name': self.name,
            'piece': self.piece,
            'offset': self.offset,
            'octave_shift': self.octave_shift,
            'instrument': self.instrument,
            'channel': self.channel,
            'velocity': self.velocity,
            'muted': self.muted,
            'channel': self.channel
        }

    def __setstate__(self, data):
        for attr in data:
            setattr(self, attr, data[attr])

        assert channel > 0 and channel < 17
        assert velocity > 0 and velocity <= 110

    def increase_velocity(self):
        self.velocity = min(self.velocity + 10, 110)

    def decrease_velocity(self):
        self.velocity = max(self.velocity - 10, 0)

    def mute(self):
        self.muted = not self.muted

    def play_note(self, note):
        logger.debug('playing note {}'.format(note))

        self.conductor.audio.play(note, self.channel, self.velocity)
        self.timers[str(note)] = self.conductor.scheduler.enter(note.duration * TIC_DURATION, 1, self.stop_note, (note,))
        self.simultaneous_play_count[str(note)] += 1

    def stop_note(self, note, *args):
        self.simultaneous_play_count[str(note)] -= 1
        if self.simultaneous_play_count[str(note)] == 0:
            self.conductor.audio.stop(note, self.channel)

    def finish(self):
        pass