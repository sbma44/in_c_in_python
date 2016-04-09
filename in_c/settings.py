import os.path

AUDIO_SERVER = {'host': '127.0.0.1', 'port': 8000}

INC_PIECE_DIR = os.path.join(os.path.dirname(__file__), 'src', 'InC')
INC_SOURCE = os.path.join(os.path.dirname(__file__), 'src', 'InC.json')

TICS_PER_MINUTE = 400 # sixteenth notes
TIC_DURATION = 60.0 / TICS_PER_MINUTE

NUM_PLAYERS = 4

