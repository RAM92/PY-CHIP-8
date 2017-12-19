from curses import wrapper

SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32

FULL_BLOCK_CHAR = u"\u2588"
EMPTY_BLOCK_CHAR = ' '

FONT = [
    [  # 0
        0xF0,
        0x90,
        0x90,
        0x90,
        0xF0
    ],
    [  # 1
        0x20,
        0x60,
        0x20,
        0x20,
        0x70,
    ],
    [  # 2
        0xF0,
        0x10,
        0xF0,
        0x80,
        0xF0,
    ],
    [  # 3
        0xF0,
        0x10,
        0xF0,
        0x10,
        0xF0,
    ],
    [  # 4
        0x90,
        0x90,
        0xF0,
        0x10,
        0x10,
    ],
    [  # 5
        0xF0,
        0x80,
        0xF0,
        0x10,
        0xF0,
    ],
    [  # 6
        0xF0,
        0x80,
        0xF0,
        0x90,
        0xF0,
    ],
    [  # 7
        0xF0,
        0x10,
        0x20,
        0x40,
        0x40,
    ],
    [  # 8
        0xF0,
        0x90,
        0xF0,
        0x90,
        0xF0,
    ],
    [  # 9
        0xF0,
        0x90,
        0xF0,
        0x10,
        0xF0,
    ],
    [  # A
        0xF0,
        0x90,
        0xF0,
        0x90,
        0x90,
    ],
    [  # B
        0xE0,
        0x90,
        0xE0,
        0x90,
        0xE0,
    ],
    [  # C
        0xF0,
        0x80,
        0x80,
        0x80,
        0xF0,
    ],
    [  # D
        0xE0,
        0x90,
        0x90,
        0x90,
        0xE0,
    ],
    [  # E
        0xF0,
        0x80,
        0xF0,
        0x80,
        0xF0,
    ],
    [  # F
        0xF0,
        0x80,
        0xF0,
        0x80,
        0x80,
    ],
]


class Screen:

    def __init__(self, show_debug=True):
        self.show_debug = show_debug
        wrapper(self.main)

    def main(self, stdscr):
        import curses
        if curses.LINES < SCREEN_HEIGHT or curses.COLS < SCREEN_WIDTH:
            raise RuntimeError('Terminal width or height insufficient!')

        stdscr.clear()
        curses.curs_set(0)
        self.stdscr = stdscr
        self.add_pixels()

        self.write_sprite(0, 0, FONT[0xa])
        self.write_sprite(0, 0, FONT[0xF])

        while True:
            pass

    def add_pixels(self):
        self.pixels = [ ([False] * SCREEN_HEIGHT) for i in range(SCREEN_WIDTH) ]

    def write_sprite(self, x, y, sprite_data: list):
        sprite_length = len(sprite_data)
        if sprite_length > 15:
            sprite_length = 15

        for y_delta in range(sprite_length):
            self.write_pixel(x + 0, y + y_delta, bool(sprite_data[y_delta] & 0x80))
            self.write_pixel(x + 1, y + y_delta, bool(sprite_data[y_delta] & 0x40))
            self.write_pixel(x + 2, y + y_delta, bool(sprite_data[y_delta] & 0x20))
            self.write_pixel(x + 3, y + y_delta, bool(sprite_data[y_delta] & 0x10))
            self.write_pixel(x + 4, y + y_delta, bool(sprite_data[y_delta] & 0x08))
            self.write_pixel(x + 5, y + y_delta, bool(sprite_data[y_delta] & 0x04))
            self.write_pixel(x + 6, y + y_delta, bool(sprite_data[y_delta] & 0x02))
            self.write_pixel(x + 7, y + y_delta, bool(sprite_data[y_delta] & 0x01))

        self.refresh()

    def write_pixel(self, x: int, y: int, on=False) -> bool:
        x %= SCREEN_WIDTH
        y %= SCREEN_HEIGHT

        previous_pixel_value = self.pixels[x][y]
        on = on != self.pixels[x][y]
        self.pixels[x][y] = on
        self.stdscr.addstr(y, x, FULL_BLOCK_CHAR if on else EMPTY_BLOCK_CHAR)

        return previous_pixel_value == self.pixels[x][y]

    def refresh(self):
        self.stdscr.refresh()