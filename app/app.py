# Implemented according to:
# http://mattmik.com/files/chip8/mastering/chip8.html


import random


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
        self.f  = (data & 0xf000) >> 12 #f for "First nibble"
        self.x  = (data & 0x0f00) >> 8
        self.y  = (data & 0x00f0) >> 4
        self.e  =  data & 0x000f
        self.nnn=  data & 0x0fff

    @property
    def nn(self):
        return self.data & 0xff


class OperationDefinition:

    match_number = 0xffff
    mask = 0

    def __init__(self, format_str, cb):
        self.str = format_str
        self.cb = cb

        self.match_number = 0
        self.mask = 0

        for i, ch in enumerate(reversed(format_str)):
            bit_position = i * 4
            try:
                x = int(ch, 16)
                self.mask |= (0xf << bit_position)
                self.match_number |= (x << bit_position)
            except ValueError:
                x = 0

    def responds_to(self, x):
        return x & self.mask == self.match_number

    def __call__(self, x):
        if self.responds_to(x):
            self.cb(Instruction(x))
            return 1
        else:
            return 0


class Memory(list):

    def __init__(self, data=[]):
        interpreter = [random.randint(0, 255) for x in range(0x200)]
        super(Memory, self).__init__(interpreter)
        self.extend(data)


class CPU(object):
    #program starts at 0x200
    #big endian - MSB first!


    @property
    def vf(self):
        return self.v[0xf]

    def __init__(self, data=[]):
        self.v=[]
        self.pc=0x200
        self.memory = Memory(data)
        self.stack = []
        for x in range(0, 16):
            self.v.append(Register())

        self.supported_operations = (
            OperationDefinition('6XNN', self.add_nn_to_vx_modulo),
            OperationDefinition('8XY0', self.store_vy_in_vx),
            OperationDefinition('7XNN', self.add_nn_to_vx),
            OperationDefinition('8XY4', self.add_vy_to_vx),
            OperationDefinition('8XY5', self.subtract_vy_from_vx),
            OperationDefinition('8XY7', self.store_vy_sub_vx_in_vx),

            OperationDefinition('8XY2', self.vx_and_vy_store_in_vx),
            OperationDefinition('8XY1', self.vx_or_vy_store_in_vx),
            OperationDefinition('8XY3', self.vx_xor_vy_store_in_vx),

            OperationDefinition('8XY6', self.shift_vy_right_store_in_vx),
            OperationDefinition('8XYE', self.shift_vy_left_store_in_vx),

            OperationDefinition('CXNN', self.set_vx_random_masked),

            OperationDefinition('1NNN', self.jump_to_nnn),
            OperationDefinition('BNNN', self.jump_to_nnn_plus_v0),

            OperationDefinition('2NNN', self.exec_subroutine),
            OperationDefinition('00EE', self.return_from_subroutine),

            OperationDefinition('0NNN', self.unsupported_operation),
        )

    def push_stack(self):
        self.stack.append(self.pc)

    def pop_stack(self):
        self.pc = self.stack.pop()

    def bool_vf(self, b):
        self.vf.value = 1 if b else 0

    def unsupported_operation(self, inst):
        raise NotImplementedError

    def add_nn_to_vx_modulo(self, inst):
        self.v[inst.x].value = inst.nn

    def store_vy_in_vx(self, inst):
        self.v[inst.x].value = self.v[inst.y].value

    def add_nn_to_vx(self, inst):
        self.v[inst.x].value += inst.nn

    def add_vy_to_vx(self, inst):
        vx_pre_op = self.v[inst.x]
        self.v[inst.x].value += self.v[inst.y].value
        self.bool_vf(self.v[inst.x] < vx_pre_op)

    def subtract_vy_from_vx(self, inst):
        vx_pre_op = self.v[inst.x].value
        self.v[inst.x].value -= self.v[inst.y].value
        self.bool_vf(self.v[inst.x].value > vx_pre_op)

    def store_vy_sub_vx_in_vx(self, inst):
        vy_pre_op = self.v[inst.y].value
        self.v[inst.y].value = self.v[inst.x].value - vy_pre_op
        self.bool_vf(self.v[inst.y].value > vy_pre_op)

    def vx_and_vy_store_in_vx(self, inst):
        self.v[inst.x].value = self.v[inst.y].value & self.v[inst.x].value

    def vx_or_vy_store_in_vx(self, inst):
        self.v[inst.x].value = self.v[inst.y].value | self.v[inst.x].value

    def vx_xor_vy_store_in_vx(self, inst):
        self.v[inst.x].value = self.v[inst.y].value ^ self.v[inst.x].value

    def shift_vy_right_store_in_vx(self, inst):
        self.vf.value = self.v[inst.y].value & 1
        self.v[inst.x].value = self.v[inst.y].value >> 1

    def shift_vy_left_store_in_vx(self, inst):
        self.vf.value = 1 if self.v[inst.y].value & 0x80 else 0
        self.v[inst.x].value = self.v[inst.y].value << 1

    def set_vx_random_masked(self, inst):
        self.v[inst.x].value = random.randint(0, 255) & inst.nn

    def jump_to_nnn(self, inst):
        self.pc = inst.nnn - 1

    def jump_to_nnn_plus_v0(self, inst):
        self.pc = inst.nnn + self.v[0].value - 1

    def exec_subroutine(self, inst):
        raise NotImplementedError

    def return_from_subroutine(self, inst):
        raise NotImplementedError

    def fetch_instruction(self):
        return self.memory[self.pc]

    @staticmethod
    def decode_instruction(data):
        return Instruction(data)

    def execute_instruction(self, inst):
        for handler in self.supported_operations:
            handler(inst.data)

    def __call__(self, x=None):
        if isinstance(x, int):
            self.execute_instruction(
                self.decode_instruction(x)
            )
        elif isinstance(x, Instruction):
            self.execute_instruction(x)
        elif x is None:
            self.execute_instruction(
                self.decode_instruction(
                    self.fetch_instruction()
                )
            )
        else:
            raise TypeError

        self.pc += 1