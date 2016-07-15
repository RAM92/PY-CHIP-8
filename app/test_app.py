import pytest
from app import Register, CPU, OpcodeDefinition, Instruction


class TestInstruction:

    def test_stores_nibble_0_on_e(self):
        i = Instruction(0x1234)
        assert i.e == 0x4

    def test_stores_nibble_1_on_y(self):
        i = Instruction(0x1234)
        assert i.y == 0x3

    def test_stores_nibble_2_on_x(self):
        i = Instruction(0x1234)
        assert i.x == 0x2

    def test_stores_nibble_3_on_f(self):
        i = Instruction(0x1234)
        assert i.f == 0x1

    def test_exposes_lower_two_nibbles_as_nn(self):
        i = Instruction(0x1234)
        assert i.nn == 0x34


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
        assert cpu.v[0].value == 0x00

    # 8XY4
    def test_adds_vy_to_vx(self, cpu):
        cpu.v[0].value = 10
        cpu.v[1].value = 10
        cpu(0x8104)
        assert cpu.v[0].value == 10
        assert cpu.v[1].value == 20

    # 8XY5
    def test_subtract_vy_from_vx(self, cpu):
        cpu.v[0].value = 10
        cpu.v[1].value = 10
        cpu(0x8105)
        assert cpu.v[0].value == 0
        assert cpu.v[1].value == 10

    # 8XY5
    def test_subtract_vy_from_vx_borrow(self, cpu):
        cpu.v[0].value = 10
        cpu.v[1].value = 11
        cpu(0x8105)
        assert cpu.v[0].value == 255
        assert cpu.v[1].value == 11
        assert cpu.vf.value == 1

    # 8XY7
    def test_subtract_vy_from_vx(self, cpu):
        cpu.v[0].value = 10
        cpu.v[1].value = 10
        cpu(0x8107)
        assert cpu.v[0].value == 0
        assert cpu.v[1].value == 10
        assert cpu.vf.value == 0

    # 8XY7
    def test_subtract_vy_from_vx_borrow(self, cpu):
        cpu.v[0].value = 11
        cpu.v[1].value = 10
        cpu(0x8107)
        assert cpu.v[0].value == 255
        assert cpu.v[1].value == 10
        assert cpu.vf.value == 1

class TestOpcodeDefinitionMapper:

    @pytest.mark.parametrize(['definition', 'input', 'responds'], (
            ('1xx4', 0x1234, True),
            ('1xx4', 0x1324, True),
            ('1xx4', 0x1004, True),
            ('1xx4', 0x1FF4, True),
            ('1xx4', 0xFFFF, False),
            ('1xx4', 0x0000, False),
            ('1xx4', 0x0004, False),
            ('1xx4', 0x1000, False),
            ('Foo0', 0xF000, True),
            ('Foo0', 0xF00B, False),
    ))
    def test_only_responds_to_appropriate_input(self, definition, input, responds):
        x = OpcodeDefinition(definition, lambda: None)
        assert x.responds_to(input) is responds
