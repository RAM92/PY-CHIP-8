import pytest
from app import Register, CPU, OperationDefinition, Instruction, Memory


class TestInstruction(object):

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


class TestMemory:

    def test_it_isinstance_list(self):
        m = Memory()
        assert isinstance(m, list)

    def test_it_has_dummy_interpreter_in_first_0x200(self):
        m = Memory()
        len(m) == 0x200

    def test_it_appends_anything_supplied_to_it(self):
        m = Memory([1, 2, 3, 4])
        assert len(m) == 0x204
        assert m[0x203] == 4


@pytest.fixture
def cpu():
    return CPU([0x6000 for x in range(0xfff)])


class TestCPU:

    def test_has_16_registers(self, cpu):
        assert len(cpu.v) == 16

    def test_pc_initializes_to_0x200(self, cpu):
        assert cpu.pc == 0x200

    def test_has_memory(self, cpu):
        assert isinstance(cpu.memory, Memory)

    def test_increments_pc_after_executing_inst(self, cpu):
        cpu()
        assert cpu.pc == 0x201
        cpu()
        assert cpu.pc == 0x202
        cpu()
        assert cpu.pc == 0x203

    def test_stack_stores_pc(self, cpu):
        cpu.pc = 100
        cpu.push_stack()
        cpu.pc = 200
        cpu.push_stack()
        cpu.pc = 300
        cpu.push_stack()
        cpu.stack == [100, 200, 300]

    def test_pc_restored_from_stack(self, cpu):
        cpu.stack = [100, 200, 300]
        cpu.pop_stack()
        assert cpu.pc == 300
        cpu.pop_stack()
        assert cpu.pc == 200
        cpu.pop_stack()
        assert cpu.pc == 100



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

    # 8XY1
    def test_vx_or_vy(self, cpu):
        cpu.v[0].value = 0b10101010
        cpu.v[1].value = 0b01010101
        cpu(0x8101)
        assert cpu.v[1].value == 0b11111111

    # 8XY2
    def test_vx_and_vy(self, cpu):
        cpu.v[0].value = 0b10101110
        cpu.v[1].value = 0b01010101
        cpu(0x8102)
        assert cpu.v[1].value == 0b00000100

    # 8XY3
    def test_vx_xor_vy(self, cpu):
        cpu.v[0].value = 0b10101110
        cpu.v[1].value = 0b01010101
        cpu(0x8103)
        assert cpu.v[1].value == 0b11111011

    # 8XY6
    def test_shift_right(self, cpu):
        cpu.v[0].value = 0b01110001
        cpu(0x8106)
        assert cpu.v[1].value == 0b00111000
        assert cpu.vf.value == 1
        cpu.v[0].value = 0b00111000
        cpu(0x8106)
        assert cpu.v[1].value == 0b00011100
        assert cpu.vf.value == 0

    # 8XYE
    def test_shift_left(self, cpu):
        cpu.v[0].value = 0b10001110
        cpu(0x810E)
        assert cpu.v[1].value == 0b00011100
        assert cpu.vf.value == 1
        cpu.v[0].value = 0b00011100
        cpu(0x810E)
        assert cpu.v[1].value == 0b00111000
        assert cpu.vf.value == 0

    # CXNN
    def test_random_number_masked(self, cpu, monkeypatch):
        import random
        monkeypatch.setattr(random, 'randint', lambda x, y: 123)
        cpu(0xC00F)
        assert cpu.v[0].value == 0b1011

    # 1NNN
    def test_jump_nnn(self, cpu):
        cpu(0x1123)
        assert cpu.pc == 0x123

    # BNNN
    def test_jump_nnn_plus_v0(self, cpu):
        cpu.v[0].value = 0x23
        cpu(0xB100)
        assert cpu.pc == 0x123

    # 2NNN
    def test_exec_subroutine(self, cpu):
        cpu(0x2500)
        assert cpu.stack == [0x200]
        assert cpu.pc == 0x500

    # 00EE
    def test_return_from_subroutine(self, cpu):
        cpu.pc = 0x500
        cpu.stack = [0x200, 0x300, 0x400]
        cpu(0x00EE)
        assert cpu.pc == 0x400
        assert cpu.stack == [0x200, 0x300]
        cpu(0x00EE)
        assert cpu.pc == 0x300
        assert cpu.stack == [0x200]
        cpu(0x00EE)
        assert cpu.pc == 0x200
        assert cpu.stack == []


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
        x = OperationDefinition(definition, lambda: None)
        assert x.responds_to(input) is responds
