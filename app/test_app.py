import pytest
from app import Register, CPU, OpcodeDefinitionMapper


class TestRegister(object):

    def test_initial_value(self):
        r = Register()
        assert r.value == 0

    def test_setter_and_getter(self):
        r = Register()
        r.value = 123
        assert r.value == 123

    def test_coerces_to_8_bits(self):
        r = Register()
        r.value = 0xfff
        assert r.value == 0xff


@pytest.fixture
def cpu():
    return CPU()

class TestOpCodes():

    # 6XNN Store number NN in register VX
    def test_stores_in_vx(self, cpu):
        cpu(0x6012)
        assert cpu.v[0] == 0x12
        cpu(0x6345)
        assert cpu.v[3] == 0x45

    # 8XY0 Store the value of register VY in register VX
    def test_stores_vy_in_vx(self, cpu):
        cpu.v[0].value = 123
        cpu(0x8f00)
        assert cpu.vf == 123
        cpu.v[2].value = 0xb0
        cpu(0x8e20)
        assert cpu.v[0xe] == 0xb0

    # 7XNN Add the value NN to register VX
    def test_adds_nn_to_vx(self, cpu):
        cpu(0x7021)
        assert cpu.v[0] == 0x21

    # 7XNN Add the value NN to register VX - wraps arond
    def test_adds_nn_to_vx_modulo(self, cpu):
        cpu.v[0].value = 0xff
        cpu(0x7001)
        assert cpu.v[0] == 0x00

    # # 8XY4 Add the value of register VY to register VX
    # def test_add_vy_to_vx_store_vx(self, cpu):
    #     cpu('')

#
# class TestCrazyInstruction():
#
#     def test_it_kinda_works(self):
#         a = 0x8129
#         b = 0x8349
#         c = 0x8569
#
#         inst_definition = '8__9'
#
#         x = b
#         assert (inst_definition[0] == '_' or int(inst_definition[0]) << 12 == x & 0xf000) and\
#                (inst_definition[1] == '_' or int(inst_definition[1]) << 8 == x & 0x0f00) and\
#                (inst_definition[2] == '_' or int(inst_definition[2]) << 4 == x & 0x00f0) and\
#                (inst_definition[3] == '_' or int(inst_definition[3]) == x & 0x000f)


class TestOpcodeDefinitionMapper:

    def test_defaults_false(self):
        x = OpcodeDefinitionMapper()
        assert x.responds_to(0x0000) is False
        assert x.responds_to(0xFFFF) is False

    def test_only_responds_to_appropriate_input(self):
        x = OpcodeDefinitionMapper('1xx4')
        assert x.responds_to(0x1234) is True
        assert x.responds_to(0x1324) is True
        assert x.responds_to(0x1004) is True
        assert x.responds_to(0x1FF4) is True
        assert x.responds_to(0xFFFF) is False
        assert x.responds_to(0x0000) is False
