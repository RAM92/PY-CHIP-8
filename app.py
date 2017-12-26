#!/usr/bin/env python
import argparse

import time

from app.screen import Screen
from app.keypad import Keypad
from app.cpu import CPU
from curses import wrapper
import logging


parser = argparse.ArgumentParser(description='Runs a CHIP-8 ROM.')
parser.add_argument('rom', help='The path to a valid CHIP-8 ROM')
parser.add_argument('-d', '--debug', help='Log debug info to log.log', action='store_true')
args = parser.parse_args()


def main(stdscr):
    if args.debug:
        logging.basicConfig(filename='log.log', level=logging.DEBUG, filemode='w')

    s = Screen(stdscr)
    k = Keypad(stdscr)
    cpu = CPU(s, k)

    logging.info('Loading program %s', args.rom)
    with open(args.rom, 'rb') as f:
        cpu.load_program(f.read())

    logging.info('Running CPU')
    while True:
        cpu()
        time.sleep(0.01)

try:
    wrapper(main)
except KeyboardInterrupt:
    print('Goodbye!')
