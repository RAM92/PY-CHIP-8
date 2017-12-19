#!/usr/bin/env python
import argparse
from screen import screen


def main():
    parser = argparse.ArgumentParser(description='Runs a CHIP-8 ROM.')
    parser.add_argument('-d', '--debug', help='show debug info while running', action='store_true')

    args = parser.parse_args()
    s = screen()

main()
