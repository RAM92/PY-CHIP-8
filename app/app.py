#!/usr/bin/env python
import argparse

import time

from screen import screen
from cpu import CPU
from curses import wrapper
import logging


logging.basicConfig(filename='log.log', level=logging.DEBUG, filemode='w')

parser = argparse.ArgumentParser(description='Runs a CHIP-8 ROM.')
parser.add_argument('rom', help='The path to a valid CHIP-8 ROM')
parser.add_argument('-d', '--debug', help='show debug info while running', action='store_true')


def main(stdscr):

    args = parser.parse_args()
    s = screen(stdscr)
    cpu = CPU(s)

    with open(args.rom, 'rb') as f:
        cpu.load_program(f.read())

    while True:
        cpu()
        # time.sleep(0.1)

wrapper(main)
