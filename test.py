import time
import fluidsynth

fs = fluidsynth.Synth()
fs.start()

sfid = fs.sfload("/usr/local/Cellar/fluid-synth/1.1.1/test/WST25FStein_00Sep22.SF2")
fs.program_select(0, sfid, 0, 0)

fs.noteon(0, 60, 50)
fs.noteon(0, 67, 50)
fs.noteon(0, 76, 50)

time.sleep(1.0)

fs.noteoff(0, 60)
fs.noteoff(0, 67)
fs.noteoff(0, 76)

time.sleep(1.0)

fs.delete()