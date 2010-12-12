import sys
from mingus.midi import fluidsynth
from mingus.containers import Track, Bar, Composition, Note, Instrument



c = Composition()

# create track
t = Track(Instrument())

b1 = Bar()

# 4-4 time
b1.set_meter((4,4))

# # add notes
# b1.place_notes("D#-4", duration=4)
# b1.place_rest(duration=4)
# b1.place_notes("E-4", duration=4)
# b1.place_notes("F#-4", duration=4)

b1.place_notes("C-4", duration=1)

# add the bar to the track
t.add_bar(b1)

b2 = Bar()
b2.set_meter((4,4))
b2.place_notes("C-4", duration=4)
b2.place_notes("C-4", duration=4)
b2.place_notes("C-4", duration=4)
b2.place_notes("C-4", duration=4)
t.add_bar(b2)


c.add_track(t)

fluidsynth.init('./sf/steinway.sf2')
fluidsynth.play_Composition(c, bpm=100)

