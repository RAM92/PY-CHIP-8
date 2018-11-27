# Implemented according to:
# http://mattmik.com/files/chip8/mastering/chip8.html


import random, datetime
from .screen import FONT, VirtualScreen
from .keypad import Keypad
import math
import logging

logger = logging.getLogger(__name__)


class Register(object):

    def __init__(self, value=0):
        self.value=value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, x):
        self._value = 0xff & self._normalize_other(x)

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

    def __repr__(self):
        # return 'int: {0:d}  hex: {0:#x}  bin: {0:#b}'.format(self.value)
        return '{0:#x}'.format(self.value)


class IRegister(Register):

    @Register.value.setter
    def value(self, x):
        self._value = 0xfff & self._normalize_other(x)


class TimerRegister(Register):

    target_time = - float('inf')

    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)

    def get_value(self):
        now = datetime.datetime.now()
        if now > self.target_time:
            return_value = 0
        else:
            return_value = round((self.target_time - now).total_seconds())
        self.logger.debug('Returning value %s', return_value)
        return return_value

    def set_value(self, x):
        x = self._normalize_other(x)
        self.target_time = datetime.datetime.now() + datetime.timedelta(seconds=x)
        self.logger.debug('Target time set to %s', self.target_time)

    value = property(get_value, set_value)



class Instruction(object):

    def __init__(self, data=0):
        self.data = data
        # self.f   = (data & 0xf000) >> 12 #f for "First nibble"
        self.x   = (data & 0x0f00) >> 8
        self.y   = (data & 0x00f0) >> 4
        self.n   =  data & 0x000f
        self.nnn =  data & 0x0fff
        self.nn  =  data & 0x00ff


class OperationDefinition:

    match_number = 0xffff
    mask = 0

    def __init__(self, format_str, cb, description=''):
        self.str = format_str
        self.description = description
        self.cb = cb

        self.match_number = 0
        self.mask = 0

        for i, ch in enumerate(format_str):
            bit_position = i * 4
            try:
                x = int(ch, 16)
                self.mask |= (0xf000 >> bit_position)
                self.match_number |= (x << 12 - bit_position)
            except ValueError:
                pass

    def responds_to(self, x):
        return x & self.mask == self.match_number

    def __call__(self, inst: Instruction):
        if self.responds_to(inst.data):
            logger.debug('Executing instruction for %s, with data %#x - %s', self.str, inst.data, self.description)
            self.cb(inst)
            return True
        else:
            return False


class Memory(list):

    def __init__(self):
        l = FONT[:]
        while len(l) != 0x200:
            l.append(0x12)
            l.append(0x00)
        while len(l) != 4096:
            l.append(0x00)
        super(Memory, self).__init__(l)

    @staticmethod
    def sprite_for_int(i: int) -> int:
        return i * 5

    def load_data(self, data):
        for i, x in enumerate(data):
            self[0x200 + i] = x


class CPU(object):
    #program starts at 0x200
    #big endian - MSB first!

    def __init__(self, screen: VirtualScreen, keypad: Keypad):
        self.v = []
        self.pc = 0x200
        self.memory = Memory()
        self.i = IRegister()
        self.stack = []
        self.delay_timer = TimerRegister()
        self.sound_timer = TimerRegister()
        self.screen = screen
        self.keypad = keypad

        for x in range(0, 16):
            r = Register()
            self.v.append(r)
            self.__dict__['v' + format(x, 'x')] = r

        self.supported_operations = (
            OperationDefinition('6XNN', self.store_nn_in_vx,                'Store NN in VX'),
            OperationDefinition('8XY0', self.store_vy_in_vx,                'Store VY in VX'),
            OperationDefinition('7XNN', self.add_nn_to_vx,                  'Add NN to VX'),
            OperationDefinition('8XY4', self.add_vy_to_vx,                  'Add VY to VX'),
            OperationDefinition('8XY5', self.subtract_vy_from_vx,           'Subtract VY from VX'),
            OperationDefinition('8XY7', self.store_vy_sub_vx_in_vx,         'Store VY - VX in VX'),

            OperationDefinition('8XY2', self.vx_and_vy_store_in_vx,         'Store VX & VY in VX'),
            OperationDefinition('8XY1', self.vx_or_vy_store_in_vx,          'Store VX | VY in VX'),
            OperationDefinition('8XY3', self.vx_xor_vy_store_in_vx,         'Store VX ^ VY in VX'),

            OperationDefinition('8XY6', self.shift_vy_right_store_in_vx,    'Shift VY right, store in VX'),
            OperationDefinition('8XYE', self.shift_vy_left_store_in_vx,     'Shift VY left, store in VX'),

            OperationDefinition('CXNN', self.set_vx_random_masked,          'Set VX to random masked by NN'),

            OperationDefinition('1NNN', self.jump_to_nnn,                   'Jump to NNN'),
            OperationDefinition('BNNN', self.jump_to_nnn_plus_v0,           'Jump to NNN plus V0'),

            OperationDefinition('2NNN', self.exec_subroutine,               'Execute subroutine at NNN'),
            OperationDefinition('00EE', self.return_from_subroutine,        'Return from subroutine'),

            OperationDefinition('3XNN', self.skip_vx_eq_nn,                 'Skip if VX == NN'),
            OperationDefinition('5XY0', self.skip_vx_eq_vy,                 'Skip if VX == VY'),
            OperationDefinition('4XNN', self.skip_vx_neq_nn,                'Skip if VX != NN'),
            OperationDefinition('9XY0', self.skip_vx_neq_vy,                'Skip if VX != VY'),

            OperationDefinition('FX15', self.set_delay_timer,               'Set delay timer to VX'),
            OperationDefinition('FX18', self.set_sound_timer,               'Set sound timer to VX'),
            OperationDefinition('FX07', self.delay_timer_to_vx,             'Set VX to value in delay timer'),

            OperationDefinition('ANNN', self.store_nnn_in_i,                'Set I to NNN'),
            OperationDefinition('FX1E', self.add_vx_to_i,                   'Add VX to I'),

            OperationDefinition('FX33', self.convert_vx_to_bcd,             'Store BCD of VX at I, I+1 and I+2'),

            OperationDefinition('FX55', self.v0_to_vx_to_memory,            'Dump V0-VX at address I'),
            OperationDefinition('FX65', self.memory_to_v0_to_vx,            'Restore V0-VX from address I'),

            OperationDefinition('DXYN', self.draw_sprite,                   'Draw sprite at address I at VX VY'),
            OperationDefinition('00E0', self.clear_screen,                  'Clear the screen'),
            OperationDefinition('FX29', self.set_i_to_font_for_vx,          'Set I to the font character for VX'),

            OperationDefinition('FX0A', self.wait_for_keypad_store_in_vx,   'Wait for keypad input, store result in VX'),
            OperationDefinition('EX9E', self.skip_if_vx_eq_key_pressed,     'Skip if VX == key pressed'),
            OperationDefinition('EXA1', self.skip_if_vx_neq_key_pressed,    'Skip if VX != key pressed'),

            OperationDefinition('0NNN', self.unsupported_operation,         'Execute native code - UNSUPPORTED'),
        )

    def load_program(self, program):
        self.memory.load_data(program)

    @staticmethod
    def bcd(x: int) -> tuple:
        x &= 0xff
        a = x % 10
        x -= a
        b = math.floor(x % 100 / 10)
        x -= b * 10
        c = math.floor(x / 100)
        return c, b, a

    def inc_pc(self):
        self.pc += 2

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
        # http://devernay.free.fr/hacks/chip8/C8TECH10.HTM#8xy7
        vy_pre_op = self.v[inst.y].value
        self.v[inst.y].value = self.v[inst.x].value - vy_pre_op # This looks wrong!!!
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
        self.inc_pc()

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

    def set_delay_timer(self, inst: Instruction):
        self.delay_timer.value = self.v[inst.x]
        self.inc_pc()

    def set_sound_timer(self, inst: Instruction):
        self.sound_timer.value = self.v[inst.x]
        self.inc_pc()

    def delay_timer_to_vx(self, inst: Instruction):
        self.v[inst.x].value = self.delay_timer.value
        self.inc_pc()

    def store_nnn_in_i(self, inst: Instruction):
        self.i.value = inst.nnn
        self.inc_pc()

    def add_vx_to_i(self, inst: Instruction):
        self.i.value = self.v[inst.x].value + self.i.value
        self.inc_pc()

    def convert_vx_to_bcd(self, inst: Instruction):
        if self.i.value + 2 >= len(self.memory):
            x = self.bcd(self.v[inst.x].value)
            self.memory[self.i.value + 0] = x[0]
            self.memory[self.i.value + 1] = x[1]
            self.memory[self.i.value + 2] = x[2]
        self.inc_pc()

    def v0_to_vx_to_memory(self, inst: Instruction):
        for i, v in enumerate(self.v):
            self.memory[self.i.value + i] = v.value
            if i == inst.x:
                break
        # self.i.value += inst.x + 1
        self.inc_pc()

    def memory_to_v0_to_vx(self, inst: Instruction):
        for i, v in enumerate(self.v):
            v.value = self.memory[self.i.value + i]
            if i == inst.x:
                break
        # self.i.value += inst.x + 1
        self.inc_pc()

    def draw_sprite(self, inst: Instruction):
        sprite_data = self.memory[self.i.value:self.i.value + inst.n]
        new_vf = self.screen.write_sprite(self.v[inst.x].value, self.v[inst.y].value, sprite_data)
        self.bool_vf(new_vf)
        self.inc_pc()

    def clear_screen(self, inst: Instruction):
        self.screen.clear()
        self.inc_pc()

    def set_i_to_font_for_vx(self, inst: Instruction):
        self.i.value = self.memory.sprite_for_int(self.v[inst.x].value)
        self.inc_pc()

    def wait_for_keypad_store_in_vx(self, inst: Instruction):
        key_value = self.keypad.read_key()
        if key_value is not None:
            self.v[inst.x].value = key_value
            self.inc_pc()

    def skip_if_vx_eq_key_pressed(self, inst: Instruction):
        self._double_inc_pc_when(self.v[inst.x].value == self.keypad.read_key())

    def skip_if_vx_neq_key_pressed(self, inst: Instruction):
        self._double_inc_pc_when(self.v[inst.x].value != self.keypad.read_key())

    ###################################################################

    def fetch_instruction(self):
        logger.debug('Fetched instruction from %#x', self.pc)
        return ((self.memory[self.pc]) << 8) | (self.memory[self.pc + 1])

    @staticmethod
    def decode_instruction(data):
        return Instruction(data)

    def execute_instruction(self, inst: Instruction):
        logger.debug('V Registers: %s', self.v)
        logger.debug('I Register: %s', self.i)
        logger.debug('Stack: %s', self.stack)
        for handler in self.supported_operations:
            success = handler(inst)
            if success:
                return
        self.unsupported_operation(inst)


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
