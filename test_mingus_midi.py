import sys
from mingus.midi import MidiFileIn
from mingus.midi import fluidsynth
from mingus.containers import Track, Bar


def print_tracks(comp):
    for t in comp.tracks:
        print t


def clean_empty_tracks(comp):
	good_tracks = []
	for t in comp.tracks:
		if t.instrument is None and len(t.bars[0])==0:
			continue
		good_tracks.append(t)
	comp.tracks = good_tracks
	return comp

fluidsynth.init('./sf/steinway.sf2')

start = 1
if len(sys.argv)>1:
    start = int(sys.argv[1])

for i in range(start, 54):
    print i
    (comp, bpm) = MidiFileIn.MIDI_to_Composition('./midi/InC-Music/%s.mid' % str(i))
    comp = clean_empty_tracks(comp)
    while True:
        for t in comp.tracks:
            print t
        fluidsynth.play_Composition(comp, bpm=bpm)
        x = raw_input("c to repeat >")
        if x.strip().lower()=="c":
            break