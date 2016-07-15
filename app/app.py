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
            OpcodeDefinition('8XY5', self.__subtract_vy_from_vx),
            OpcodeDefinition('8XY7', self.__store_vy_sub_vx_in_vx),

            OpcodeDefinition('8XY2', self.__vx_and_vy_store_in_vx),
            OpcodeDefinition('8XY1', self.__vx_or_vy_store_in_vx),
            OpcodeDefinition('8XY3', self.__vx_xor_vy_store_in_vx),

            OpcodeDefinition('8XY6', self.__shift_vy_right_store_in_vx),
            OpcodeDefinition('8XYE', self.__shift_vy_left_store_in_vx),

            OpcodeDefinition('CXNN', self.__set_vx_random_masked),

            OpcodeDefinition('1NNN', self.__jump_to_nnn),
            OpcodeDefinition('BNNN', self.__jump_to_nnn_plus_v0),

            OpcodeDefinition('2NNN', self.__exec_subroutine),
            OpcodeDefinition('00EE', self.__return_from_subroutine),

            OpcodeDefinition('0NNN', self.__unsupported_operation),
        )

    def __bool_vf(self, b):
        self.vf.value = 1 if b else 0

    def __unsupported_operation(self, inst):
        raise NotImplementedError

    def __add_nn_to_vx_modulo(self, inst):
        self.v[inst.x].value = inst.nn

    def __store_vy_in_vx(self, inst):
        self.v[inst.x].value = self.v[inst.y].value

    def __add_nn_to_vx(self, inst):
        self.v[inst.x].value += inst.nn

    def __add_vy_to_vx(self, inst):
        vx_pre_op = self.v[inst.x]
        self.v[inst.x].value += self.v[inst.y].value
        self.__bool_vf(self.v[inst.x] < vx_pre_op)

    def __subtract_vy_from_vx(self, inst):
        vx_pre_op = self.v[inst.x].value
        self.v[inst.x].value -= self.v[inst.y].value
        self.__bool_vf(self.v[inst.x].value > vx_pre_op)

    def __store_vy_sub_vx_in_vx(self, inst):
        vy_pre_op = self.v[inst.y].value
        self.v[inst.y].value = self.v[inst.x].value - vy_pre_op
        self.__bool_vf(self.v[inst.y].value > vy_pre_op)

    def __vx_and_vy_store_in_vx(self, inst):
        raise NotImplementedError

    def __vx_or_vy_store_in_vx(self, inst):
        raise NotImplementedError

    def __vx_xor_vy_store_in_vx(self, inst):
        raise NotImplementedError

    def __shift_vy_right_store_in_vx(self, inst):
        raise NotImplementedError

    def __shift_vy_left_store_in_vx(self, inst):
        raise NotImplementedError

    def __set_vx_random_masked(self, inst):
        raise NotImplementedError

    def __jump_to_nnn(self, inst):
        raise NotImplementedError

    def __jump_to_nnn_plus_v0(self, inst):
        raise NotImplementedError

    def __exec_subroutine(self, inst):
        raise NotImplementedError

    def __return_from_subroutine(self, inst):
        raise NotImplementedError

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
