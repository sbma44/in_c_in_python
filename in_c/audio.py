import liblo
from in_c.settings import *

class OSC2MIDI(object):
    """ OSC/MIDI Bridge """
    def __init__(self, host='127.0.0.1', port=8000):
        self.target = liblo.Address(host, port)

    def play(self, note, channel, velocity=70):
        msg = liblo.Message('/osc/midi/out/noteOn/{}'.format(channel))
        msg.add(('i', note.midi))
        msg.add(('i', velocity))
        msg.add(('i', 1))
        liblo.send(self.target, msg)

    def stop(self, note, channel):
        msg = liblo.Message('/osc/midi/out/noteOff/{}'.format(channel))
        msg.add(('i', note.midi))
        msg.add(('i', 120))
        msg.add(('i', 0))
        liblo.send(self.target, msg)