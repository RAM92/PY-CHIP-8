# Implemented according to:
# http://mattmik.com/files/chip8/mastering/chip8.html



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
        self.e  =  data & 0x000f

    @property
    def nn(self):
        return self.data & 0xff


class OpcodeDefinition:

    match_number = 0xffff
    mask = 0

    def __init__(self, format_str, cb):
        self.str = format_str
        self.cb = cb

        match_number = 0
        mask = 0

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

    def __call__(self, x):
        if self.responds_to(x):
            self.cb(Instruction(x))
            return 1
        else:
            return 0


class Memory(list):

    def __init__(self):
        self.regions = [
            ((0, 0), self.get_random, 'interpreter'),
        ]

    @staticmethod
    def get_random(self):
        return 0


# def get_supported_operations():
#     ops = []
#
#     def for_spec(spec):
#         def for_spec_inner(fn):
#             ops.append({spec: fn})
#             return fn
#
#         return for_spec_inner
#
#     @for_spec('1234')
#     def foo(cpu, inst):
#         pass
#
#     return ops

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

        self.supported_operations = (
            OpcodeDefinition('6XNN', self.__add_nn_to_vx_modulo),
            OpcodeDefinition('8XY0', self.__store_vy_in_vx),
            OpcodeDefinition('7XNN', self.__add_nn_to_vx),
            OpcodeDefinition('8XY4', self.__add_vy_to_vx),
        )

    def __add_nn_to_vx_modulo(self, inst):
        self.v[inst.x].value = inst.nn

    def __store_vy_in_vx(self, inst):
        self.v[inst.x].value = self.v[inst.y].value

    def __add_nn_to_vx(self, inst):
        self.v[inst.x].value += inst.nn

    def __add_vy_to_vx(self, inst):
        vx_pre_op = self.v[inst.x]
        self.v[inst.x].value += self.v[inst.y].value
        if self.v[inst.x] < vx_pre_op:
            self.vf.value = 1
        else:
            self.vf.value = 0

    def fetch_instruction(self):
        raise NotImplementedError

    @staticmethod
    def decode_instruction(data):
        return Instruction(data)

    def execute_instruction(self, inst):
        for handler in self.supported_operations:
            handler(inst.data)

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
