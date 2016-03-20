import rtmidi_python as rtmidi
from in_c.settings import *

class OSC2MIDI(object):
    """ OSC/MIDI Bridge """
    def __init__(self, host='127.0.0.1', port=8000):
        self.midi = rtmidi.MidiOut()
        self.midi.open_virtual_port('in_c')

    def play(self, note, channel, velocity=70):
        self.midi.send_message([min(159, 143 + channel), note.midi, velocity])

    def stop(self, note, channel):
        self.midi.send_message([min(143, 127 + channel), note.midi, 70])
