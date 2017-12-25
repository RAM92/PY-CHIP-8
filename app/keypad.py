import logging

logger = logging.getLogger(__name__)

KEY_MAPPING = {
    '1': 0x1,
    '2': 0x2,
    '3': 0x3,
    'q': 0x4,
    'w': 0x5,
    'e': 0x6,
    'a': 0x7,
    's': 0x8,
    'd': 0x9,
    'x': 0x0,
    'z': 0xa,
    'c': 0xb,
    '4': 0xc,
    'r': 0xd,
    'f': 0xe,
    'v': 0xf,
}


class Keypad:

    def __init__(self, stdscr):
        self.stdscr = stdscr
        stdscr.nodelay(True)

    def read_key(self):
        try:
            key = self.stdscr.getkey()
        except:
            key = None
        return_value = KEY_MAPPING.get(key, None)
        logger.debug('Returning value %s', return_value)
        return return_value
