import sys
import time
import os
import signal
import multiprocessing
import json
import signal
from functools import partial

import logging
logging.basicConfig()
logger = logging.getLogger('in_c')
logger.setLevel(logging.INFO)

import pyuv

import in_c.audio
import in_c.web
import in_c.music
import in_c.player

from in_c.settings import *

class Conductor(object):
    def __init__(self):
        super(Conductor, self).__init__()

        # set performance constants
        self.tic_count = 0
        self.time_interval = 60.0 / (TICS_PER_MINUTE * 1.0)

        # load music
        self.pieces = in_c.music.load()
        self.piece_events = in_c.music.build(self.pieces)

        # interprocess stuff
        self.web_process = None
        self.web_q = multiprocessing.Queue()
        self.inc_q = multiprocessing.Queue()

        # event loop
        self.loop = pyuv.Loop.default_loop()

        # initialize player objects
        self.players = {}
        for i in range(0, NUM_PLAYERS):
            player = in_c.player.Player(conductor=self, channel=(i+1))
            self.players[player.uuid] = player

        # create MIDI bridge
        self.audio = in_c.audio.OSC2MIDI(host=OSC_SERVERS[0]['host'], port=OSC_SERVERS[0]['port'])

    def check_messages(self):
        messages = []
        while not self.inc_q.empty():
            try:
                messages.append(self.inc_q.get(False))
            except:
                pass
        return messages

    def send_state(self):
        m = { '_': 'state_xfer', 'players': {} }
        for (i, p) in enumerate(self.players):
            m['players'][p.uuid] = pickle.dumps(p)
        self.web_q.put(m)

    def create_dummy_players(self):
        for (i, player_uuid) in enumerate(self.players):
            self.players[player_uuid].piece = i
            self.players[player_uuid].channel = i + 1
            self.players[player_uuid].offset = 0
            self.players[player_uuid].name = 'Player {}'.format(i)

    def lobby(self):
        pass

    def handle_messages(self):
        msgs = self.check_messages()
        for (m, src) in msgs:
            action = m['_']

            if action=='toggle':
                player = self.players.get(m.get('uuid'))
                if player:
                    player.mute()
                self.send_state()

            elif action=='state_xfer':
                for player_state in m['players']:
                    self.players[player_state.uuid].__setstate__(player_state)

            elif action=='status':
                self.send_state()

            elif action=='decode_failure':
                LOGGER.warn('Failed to decode JSON message: {}'.format(src))

    def tic(self, timer_handle):
        logger.debug('tic %d', self.tic_count)
        for (i, player_uuid) in enumerate(self.players):
            player = self.players[player_uuid]
            if player.piece is None or player.muted:
                continue

            events = self.piece_events[player.piece][(self.tic_count + player.offset) % len(self.piece_events[player.piece])]
            if events is None:
                continue
            else:
                for note in events:
                    player.play_note(note)

        self.handle_messages()

        self.tic_count = self.tic_count + 1

    def start(self):
        self.tic_timer = pyuv.Timer(self.loop)
        self.tic_timer.start(self.tic, 0, TIC_DURATION)
        self.loop.run()

    def start_web(self):
        self.web_process = multiprocessing.Process(target=in_c.web.start, args=(self.inc_q, self.web_q))
        self.web_process.daemon = True
        self.web_process.start()

    def finish(self, *args):
        if hasattr(self, 'finished'):
            return

        logger.info('Stopping')

        if hasattr(self, 'tic_timer'):
            self.tic_timer.stop()

        for player_uuid in self.players:
            self.players[player_uuid].finish()

        if self.web_process.is_alive():
            self.web_process.terminate()

        self.finished = True


def main():
    conductor = Conductor()

    # clean up on SIGINT
    signal.signal(signal.SIGINT, conductor.finish)

    conductor.create_dummy_players()

    logger.info('Starting web server...')
    conductor.start_web()

    logger.info('Running lobby...')
    conductor.lobby()

    try:
        logger.info('Starting main loop...')
        conductor.start()
    except Exception as e:
        raise e
    finally:
        conductor.finish()

if __name__ == '__main__':
    main()