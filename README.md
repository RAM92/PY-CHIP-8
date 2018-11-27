
# PY-CHIP-8

## Setup
Ensure you have python version 3, pip and virtualenv available in your
environment.

To setup the project, run:

```bash
virtualenv -p $(which python) env
source env/bin/activate
pip install -r requirements.txt
```

## Project motivation
[CHIP-8](https://en.wikipedia.org/wiki/CHIP-8) is a simple virtual machine,
used primarily for running simple games on old computers.
It is also the de facto "first emulator project". Seeing as it has never
existed in hardware format (other than a few FPGA implementations by hobbyists),
a lot of the implementation details are left to the developer.

## Method Justification
I had recently started working with Python, and this project was to give
me a nice opportunity to exercise what I have recently learned, without
pushing me too far out of my comfort zone. In other words, I know it will
be pretty straight-forward, making for some excellent bed time programming.
...Why are you looking at me like that?

In addition to this, Python has a Curses library built right into it
(for darwin and linux... sorry windows users!) with a very clean API,
making this an excellent choice for implementing the graphics.
Performance isn't even a consideration for this VM, ~~as it only needs to
operate at a laughable 60Hz.~~ EDIT: I'm not sure this is true, cannot
remember where I got that figure from... but it can get away with being slow
AF.
