
#VM-PY-CHIP-8

##Project motivation
CHIP-8 is a simple virtual machine, used primarily for running simple games on old computers. It is also the de facto "first emulator project". Seeing as it has never existed in hardware format (other than a few FPGA implementations by hobbyists), a lot of the implementation is left to the developer.

##Proposed Tools
##Python

##Py-test



##Method Justification
I have recently started working with Python, and this will give me a nice opportunity to exercise what I have recently learned, without pushing me too far out of my comfort zone. In other words, I know it will be pretty straight-forward, making for some excellent bed time programming. ...Why are you looking at me like that?

In addition to this, Python has a Curses library built right into it with a very clean API, making this an excelent choice for implementing the graphics. Performance isn't even a consideration for this VM, as it only needs to operate at a laughable 60Hz.