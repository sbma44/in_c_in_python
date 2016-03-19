import OSC
from settings import *

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