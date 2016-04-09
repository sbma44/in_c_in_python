import socket, socketserver
import json

import rtmidi_python as rtmidi

from in_c.music import NoteEvent
from in_c.settings import *

class AudioReceiver(object):
    def __init__(self, *args):
        self.midi = rtmidi.MidiOut()
        self.midi.open_virtual_port('in_c')

        self.server = socketserver.TCPServer(('localhost', AUDIO_SERVER['port']), self.AudioReceiverHandler)
        self.server.midi = self.midi

    def start(self):
        self.server.serve_forever()

    class AudioReceiverHandler(socketserver.StreamRequestHandler):
        def play(self, note, channel, velocity=70):
            self.server.midi.send_message([min(159, 143 + channel), note, velocity])

        def stop(self, note, channel):
            self.server.midi.send_message([min(143, 127 + channel), note, 70])

        def handle(self, *args):
            b = self.rfile.readline()

            if len(b) == 0:
                return

            data = json.loads(b.decode('utf-8').strip())

            for event in data:
                if event['play']:
                    self.play(event['note'], event['channel'], event['velocity'])
                else:
                    self.stop(event['note'], event['channel'])

            self.wfile.write(bytes('OK\n', 'utf-8'))

class AudioSender(object):
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.tic = -1
        self.buffer = []

        self.connect()

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def play(self, tic, note, channel, velocity=70):
        if tic != self.tic:
            self._send()
        self.buffer.append({ 'play': True, 'tic': tic, 'note': note.midi, 'channel': channel, 'velocity': velocity })

    def stop(self, tic, note, channel):
        if tic != self.tic:
            self._send()
        self.buffer.append({ 'play': False, 'tic': tic, 'note': note.midi, 'channel': channel })

    def _send(self):
        if len(self.buffer) == 0:
            return

        received = ''

        try:
            self.sock.sendall(bytes(json.dumps(self.buffer) + "\n", "utf-8"))
            self.tic = self.buffer[0]['tic']
            self.buffer = []

            received = str(self.sock.recv(1024), "utf-8")
        except:
            pass

        if received.strip() != 'OK':
            self.connect()

    def finish():
        self.sock.close()

def receiver_start():
    receiver = AudioReceiver()
    receiver.start()

def finish():
    # todo - daemonize on start(), kill process on this method
    pass

