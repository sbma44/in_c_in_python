import sys
from in_c.settings import *

import logging
logging.basicConfig()
logger = logging.getLogger('in_c')
logger.setLevel(logging.INFO)

if __name__ == '__main__':
    if '--receiver' in sys.argv:
        logger.info('starting receiver on {}:{}'.format(AUDIO_SERVER['host'], AUDIO_SERVER['port']))
        import in_c.audio
        in_c.audio.receiver_start()
    else:
        logger.info('starting conductor')
        import in_c.conductor
        in_c.conductor.start()