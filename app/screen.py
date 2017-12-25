import logging

logger = logging.getLogger(__name__)

SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32

FULL_BLOCK_CHAR = u"\u2588"
EMPTY_BLOCK_CHAR = ' '

FONT = [
    0xF0,
    0x90,
    0x90,
    0x90,
    0xF0,

    0x20,
    0x60,
    0x20,
    0x20,
    0x70,

    0xF0,
    0x10,
    0xF0,
    0x80,
    0xF0,

    0xF0,
    0x10,
    0xF0,
    0x10,
    0xF0,

    0x90,
    0x90,
    0xF0,
    0x10,
    0x10,

    0xF0,
    0x80,
    0xF0,
    0x10,
    0xF0,

    0xF0,
    0x80,
    0xF0,
    0x90,
    0xF0,

    0xF0,
    0x10,
    0x20,
    0x40,
    0x40,

    0xF0,
    0x90,
    0xF0,
    0x90,
    0xF0,

    0xF0,
    0x90,
    0xF0,
    0x10,
    0xF0,

    0xF0,
    0x90,
    0xF0,
    0x90,
    0x90,

    0xE0,
    0x90,
    0xE0,
    0x90,
    0xE0,

    0xF0,
    0x80,
    0x80,
    0x80,
    0xF0,

    0xE0,
    0x90,
    0x90,
    0x90,
    0xE0,

    0xF0,
    0x80,
    0xF0,
    0x80,
    0xF0,

    0xF0,
    0x80,
    0xF0,
    0x80,
    0x80,
]


class VirtualScreen:

    def __init__(self):
        self._write_pixels()

    def _write_pixels(self):
        self.pixels = [([False] * SCREEN_HEIGHT) for i in range(SCREEN_WIDTH)]

    def write_sprite(self, x, y, sprite_data: list):
        logger.debug('writing sprite at x:%s y:%s with data %s', x, y, sprite_data)
        sprite_length = len(sprite_data)
        if sprite_length > 15:
            sprite_length = 15

        return_value = False
        for y_delta in range(sprite_length):
            return_value = self.write_pixel(x + 0, y + y_delta, bool(sprite_data[y_delta] & 0x80)) or return_value
            return_value = self.write_pixel(x + 1, y + y_delta, bool(sprite_data[y_delta] & 0x40)) or return_value
            return_value = self.write_pixel(x + 2, y + y_delta, bool(sprite_data[y_delta] & 0x20)) or return_value
            return_value = self.write_pixel(x + 3, y + y_delta, bool(sprite_data[y_delta] & 0x10)) or return_value
            return_value = self.write_pixel(x + 4, y + y_delta, bool(sprite_data[y_delta] & 0x08)) or return_value
            return_value = self.write_pixel(x + 5, y + y_delta, bool(sprite_data[y_delta] & 0x04)) or return_value
            return_value = self.write_pixel(x + 6, y + y_delta, bool(sprite_data[y_delta] & 0x02)) or return_value
            return_value = self.write_pixel(x + 7, y + y_delta, bool(sprite_data[y_delta] & 0x01)) or return_value
        return return_value

    def write_pixel(self, x: int, y: int, on=False) -> bool:
        x %= SCREEN_WIDTH
        y %= SCREEN_HEIGHT
        previous_pixel_value = self.pixels[x][y]
        on = on != self.pixels[x][y]
        self.pixels[x][y] = on

        return previous_pixel_value is True and on is False

    def clear(self):
        self._write_pixels()


screen_instance = None


class _Screen(VirtualScreen):

    def __init__(self, stdscr):
        super(_Screen, self).__init__()
        import curses
        if curses.LINES < SCREEN_HEIGHT or curses.COLS < SCREEN_WIDTH:
            raise RuntimeError('Terminal width or height insufficient!')

        stdscr.clear()
        curses.curs_set(0)
        self.stdscr = stdscr

    def write_sprite(self, x, y, sprite_data: list) -> bool:
        x = super(_Screen, self).write_sprite(x, y, sprite_data)
        self.refresh()
        return x

    def write_pixel(self, x: int, y: int, on=False) -> bool:
        self.stdscr.addstr(y, x, FULL_BLOCK_CHAR if on else EMPTY_BLOCK_CHAR)
        return super(_Screen, self).write_pixel(x, y, on)

    def refresh(self):
        self.stdscr.refresh()

    def clear(self):
        self.stdscr.clear()
        self.refresh()
        super().clear()


def screen(stdscr):
    global screen_instance
    if screen_instance:
        return screen_instance
    screen_instance = _Screen(stdscr)
    return screen_instance
