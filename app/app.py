# Implemented according to:
# http://mattmik.com/files/chip8/mastering/chip8.html


import random, datetime

import math


class Register(object):

    def __init__(self, value=0):
        self.value=value

    def get_value(self):
        return self._value

    def set_value(self, x):
        self._value = 0xff & x

    value = property(get_value, set_value)

    @staticmethod
    def _normalize_other(other):
        if isinstance(other, int):
            return other
        elif isinstance(other, Register):
            return other.value
        else:
            raise TypeError

    def __eq__(self, other):
        return self.value == self._normalize_other(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __gt__(self, other):
        return self.value > self._normalize_other(other)

    def __lt__(self, other):
        return self.value < self._normalize_other(other)


class TimerRegister(Register):

    target_time = 0

    def __init__(self):
        super(TimerRegister, self).__init__()

    @staticmethod
    def get_now_ticks():
        return datetime.datetime.now().timestamp()

    def get_value(self):
        now = self.get_now_ticks()
        if now > self.target_time:
            return 0
        else:
            return int(self.target_time - now)

    def set_value(self, x):
        self.target_time = self.get_now_ticks() + (x & 0xff)

    value = property(get_value, set_value)



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
            return True
        else:
            return False


class Memory(list):

    def __init__(self, data=[]):
        interpreter = [random.randint(0, 255) for x in range(0x200)]
        super(Memory, self).__init__(interpreter)
        self.extend(data)


class CPU(object):
    #program starts at 0x200
    #big endian - MSB first!

    def __init__(self, data=[]):
        self.v=[]
        self.pc=0x200
        self.memory = Memory(data)
        self.stack = []
        for x in range(0, 16):
            r = Register()
            self.v.append(r)
            self.__dict__['v' + format(x, 'x')] = r

        self.supported_operations = (
            OperationDefinition('6XNN', self.store_nn_in_vx),
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

            OperationDefinition('3XNN', self.skip_vx_eq_nn),
            OperationDefinition('5XY0', self.skip_vx_eq_vy),
            OperationDefinition('4XNN', self.skip_vx_neq_nn),
            OperationDefinition('9XY0', self.skip_vx_neq_vy),

            OperationDefinition('0NNN', self.unsupported_operation),
        )

    def inc_pc(self):
        self.pc += 1

    def push_stack(self):
        self.stack.append(self.pc)

    def pop_stack(self):
        self.pc = self.stack.pop()

    def bool_vf(self, b):
        self.vf.value = 1 if b else 0

    def unsupported_operation(self, inst):
        raise NotImplementedError('No instruction for: {0:x}'.format(inst.data))

    def store_nn_in_vx(self, inst):
        self.v[inst.x].value = inst.nn
        self.inc_pc()

    def store_vy_in_vx(self, inst):
        self.v[inst.x].value = self.v[inst.y].value
        self.inc_pc()

    def add_nn_to_vx(self, inst):
        self.v[inst.x].value += inst.nn
        self.inc_pc()

    def add_vy_to_vx(self, inst):
        vx = self.v[inst.x]
        vx_pre_op = vx.value
        vx.value += self.v[inst.y].value
        self.bool_vf(vx < vx_pre_op)
        self.inc_pc()

    def subtract_vy_from_vx(self, inst):
        vx_pre_op = self.v[inst.x].value
        self.v[inst.x].value -= self.v[inst.y].value
        self.bool_vf(self.v[inst.x].value > vx_pre_op)
        self.inc_pc()

    def store_vy_sub_vx_in_vx(self, inst):
        vy_pre_op = self.v[inst.y].value
        self.v[inst.y].value = self.v[inst.x].value - vy_pre_op
        self.bool_vf(self.v[inst.y].value > vy_pre_op)
        self.inc_pc()

    def vx_and_vy_store_in_vx(self, inst):
        self.v[inst.x].value = self.v[inst.y].value & self.v[inst.x].value
        self.inc_pc()

    def vx_or_vy_store_in_vx(self, inst):
        self.v[inst.x].value = self.v[inst.y].value | self.v[inst.x].value
        self.inc_pc()

    def vx_xor_vy_store_in_vx(self, inst):
        self.v[inst.x].value = self.v[inst.y].value ^ self.v[inst.x].value
        self.inc_pc()

    def shift_vy_right_store_in_vx(self, inst):
        vy_value = self.v[inst.y].value
        self.vf.value = vy_value & 1
        new_vx = vy_value >> 1
        print(vy_value)
        self.v[inst.x].value = new_vx
        self.inc_pc()

    def shift_vy_left_store_in_vx(self, inst):
        self.vf.value = 1 if self.v[inst.y].value & 0x80 else 0
        self.v[inst.x].value = self.v[inst.y].value << 1
        self.inc_pc()

    def set_vx_random_masked(self, inst):
        self.v[inst.x].value = random.randint(0, 255) & inst.nn
        self.inc_pc()

    def _set_pc_new_address(self, x):
        self.pc = x

    def jump_to_nnn(self, inst):
        self._set_pc_new_address(inst.nnn)

    def jump_to_nnn_plus_v0(self, inst):
        self._set_pc_new_address(inst.nnn + self.v[0].value)

    def exec_subroutine(self, inst):
        self.push_stack()
        self._set_pc_new_address(inst.nnn)

    def return_from_subroutine(self, inst):
        self.pop_stack()

    def _double_inc_pc_when(self, condition):
        if condition:
            self.inc_pc()
        self.inc_pc()

    def skip_vx_eq_nn(self, inst):
        self._double_inc_pc_when(self.v[inst.x] == inst.nn)

    def skip_vx_eq_vy(self, inst):
        self._double_inc_pc_when(self.v[inst.x] == self.v[inst.y])

    def skip_vx_neq_nn(self, inst):
        self._double_inc_pc_when(self.v[inst.x] != inst.nn)

    def skip_vx_neq_vy(self, inst):
        self._double_inc_pc_when(self.v[inst.x] != self.v[inst.y])

    def fetch_instruction(self):
        return self.memory[self.pc]

    @staticmethod
    def decode_instruction(data):
        return Instruction(data)

    def execute_instruction(self, inst):
        for handler in self.supported_operations:
            success = handler(inst.data)
            if success:
                break

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
