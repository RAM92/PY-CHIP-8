# Implemented according to:
# http://mattmik.com/files/chip8/mastering/chip8.html


class Nibble():

    def __init__(self, value=0):
        self.value=value

    def __getattr__(self, item):
        if item[0] == 'n':
            n = int(item[1])
            bits_to_shit = n * 4
            return (self.value >> bits_to_shit) & 0xf
        else:
            return super(Nibble, self).__getattr__(item)


class Register(object):

    def __init__(self, value=0):
        self.value=value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, x):
        self._value = 0xff & x

    def __eq__(self, other):
        if isinstance(other, int):
            return self.value == other
        elif isinstance(Register):
            return self.value == other.value
        else:
            raise TypeError


class Instruction(object):

    def __init__(self, data=0):
        self.data = data
        self.f  = (data & 0xf000) >> 12 #f for "First byte"
        self.x  = (data & 0x0f00) >> 8
        self.y  = (data & 0x00f0) >> 4
        self.e  = data & 0x000f
        self.nn = data & 0x00ff


class OpcodeDefinitionMapper:

    match_number = 0xffff
    mask = 0

    def __init__(self, format_str=None, fn=None, cb=lambda: None):
        self.str = format_str
        self.fn = fn
        self.cb = cb

        match_number = 0
        mask = 0
        if isinstance(format_str, str):
            for i, ch in enumerate(reversed(format_str)):
                bit_position = i * 4
                try:
                    x = int(ch, 16)
                    mask |= (0xf << bit_position)
                    match_number |= (x << bit_position)
                except ValueError:
                    x = 0

            self.match_number = match_number
            self.mask = mask

    def responds_to(self, x):
        return x & self.mask == self.match_number


class Memory(list):

    def __init__(self):
        self.regions = [
            ((0, 0), self.get_random, 'interpreter'),
        ]

    @staticmethod
    def get_random(self):
        return 0


class CPU(object):
    #program starts at 0x200
    #big endian - MSB first!


    @property
    def vf(self):
        return self.v[0xf]

    def __init__(self):
        self.v=[]
        self.pc=0
        for x in range(0, 16):
            self.v.append(Register())
        #
        # self.responders = (
        #     (Responder(''))
        # )



    def fetch_instruction(self):
        raise NotImplementedError

    @staticmethod
    def decode_instruction(data):
        return Instruction(data)

    def execute_instruction(self, inst):
        if inst.f == 6:
            self.v[inst.x].value = inst.nn
        elif inst.f == 8:
            if inst.e == 0:
                self.v[inst.x].value = self.v[inst.y].value
            if inst.e == 4:
                vx_pre_op = self.v[inst.x]
                self.v[inst.x].value += self.v[inst.y]
                if self.v[inst.x] < vx_pre_op:
                    self.vf.value = 1
                else:
                    self.vf.value = 0
        elif inst.f == 7:
            self.v[inst.x].value += inst.nn

    def __call__(self, x):
        if isinstance(x, int):
            self.execute_instruction(
                self.decode_instruction(x)
            )
        elif isinstance(x, Instruction):
            self.execute_instruction(x)
        else:
            raise TypeError

# c = CPU()

# c.execute_instruction(Instruction(0x7012))
