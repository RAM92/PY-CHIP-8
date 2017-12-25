#!/usr/bin/env python
import argparse

import time

from screen import screen
from cpu import CPU
from curses import wrapper
import logging


parser = argparse.ArgumentParser(description='Runs a CHIP-8 ROM.')
parser.add_argument('rom', help='The path to a valid CHIP-8 ROM')
parser.add_argument('-d', '--debug', help='Log debug info to log.log', action='store_true')
args = parser.parse_args()


def main(stdscr):
    if args.debug:
        logging.basicConfig(filename='log.log', level=logging.DEBUG, filemode='w')

    s = screen(stdscr)
    cpu = CPU(s)

    with open(args.rom, 'rb') as f:
        cpu.load_program(f.read())

    while True:
        cpu()
        # time.sleep(0.1)
try:
    wrapper(main)
except KeyboardInterrupt:
    print('Goodbye!')
