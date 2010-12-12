import sys, time
from mingus.midi import fluidsynth
from mingus.containers import *

fluidsynth.init('./sf/steinway.sf2')

notes = ['B-3', 'C-4', 'D-4', 'E-4', 'F-4', 'G-4', 'A-4', 'B-4', 'C-5']

nc = NoteContainer()
for tn in notes:
    print tn
    n = Note(tn, 4)
    n.velocity = 100
    n.channel = 1
    nc += n

print nc

for (i, note) in enumerate(nc):
    fluidsynth.play_Note(note)
    time.sleep(0.2)
    if (i%2)==0:
        # fluidsynth.stop_Note(note)
        continue

time.sleep(2)

# c = Composition()
# 
# # create track
# t = Track(Instrument())
# 
# b1 = Bar()
# 
# # 4-4 time
# b1.set_meter((4,4))
# 
# # # add notes
# b1.place_notes("D#-4", duration=4)
# b1.place_rest(duration=4)
# b1.place_notes("E-4", duration=4)
# b1.place_notes("F#-4", duration=4)
# 
# b1.place_notes("C-4", duration=1)
# 
# # add the bar to the track
# t.add_bar(b1)
# # 
# # b2 = Bar()
# # b2.set_meter((4,4))
# # b2.place_notes("C-4", duration=4)
# # b2.place_notes("C-4", duration=4)
# # b2.place_notes("C-4", duration=4)
# # b2.place_notes("C-4", duration=4)
# # t.add_bar(b2)
# # 
# # 
# c.add_track(t)
# # 
# # 
# # # fluidsynth.init('./sf/steinway.sf2')
# fluidsynth.play_Composition(c, bpm=100)
# 
