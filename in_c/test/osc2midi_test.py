import unittest
import in_c.audio
import in_c.music

class OSC2MIDITest:
    osc = inc.audio.OSC2MIDI()
    note = inc.music.NoteEvent()
    channel = 1
    osc.play(note, channel)
    sleep(0.5)
    osc.stop(note, channel)
    self.assertTrue(True, 'played music')