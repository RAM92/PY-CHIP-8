import pytest
from freezegun import freeze_time
from .cpu import Register, CPU, OperationDefinition, Instruction, Memory, TimerRegister, IRegister
from datetime import datetime, timedelta

NICE_DATE = datetime(2001, 1, 1, 0, 0, 0)

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

    def test_gt(self):
        a = Register(1)
        b = Register(2)
        assert (b > a) is True
        assert (a > b) is False

    def test_lt(self):
        a = Register(1)
        b = Register(2)
        assert (b < a) is False
        assert (a < b) is True


class TestMemory:

    def test_it_isinstance_list(self):
        m = Memory()
        assert isinstance(m, list)

    def test_it_has_dummy_interpreter_in_first_0x200(self):
        m = Memory()
        len(m) == 0x200

    def test_it_returns_address_for_sprite(self):
        m = Memory()
        assert m.sprite_for_int(0x0) == 0
        assert m.sprite_for_int(0xa) == 0xa * 5
        assert m.sprite_for_int(0xf) == 0xf * 5


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

    def test_has_i_register(self, cpu):
        assert isinstance(cpu.i, IRegister)

    def test_increments_pc_after_executing_inst(self, cpu):
        cpu.memory[0x200 + 0] = 0x60
        cpu.memory[0x201 + 0] = 0x00 # 6XNN
        cpu.memory[0x202 + 0] = 0x60
        cpu.memory[0x203 + 0] = 0x00 # 6XNN
        cpu.memory[0x204 + 0] = 0x60
        cpu.memory[0x205 + 0] = 0x00 # 6XNN

        cpu()
        assert cpu.pc == 0x202
        cpu()
        assert cpu.pc == 0x204
        cpu()
        assert cpu.pc == 0x206

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
        cpu(0x7021)
        assert cpu.v[0] == 0x21 + 0x21

    # 7XNN Add the value NN to register VX - wraps around
    def test_adds_nn_to_vx_modulo(self, cpu):
        cpu.v[0].value = 0xff
        cpu(0x7001)
        assert cpu.v[0].value == 0x00

    # 8XY4 Add VY to VX - no carry
    def test_adds_vy_to_vx(self, cpu):
        cpu.v[0].value = 10
        cpu.v[1].value = 10
        cpu.v[15].value = 123
        cpu(0x8104)
        assert cpu.v[0].value == 10
        assert cpu.v[1].value == 20
        assert cpu.vf == 0

    # 8XY4 Add VY to VX - wraps around
    def test_adds_vy_to_vx_wraps(self, cpu):
        cpu.v[0].value = 0xff
        cpu.v[1].value = 10
        cpu(0x8104)
        assert cpu.v[0].value == 0xff
        assert cpu.v[1].value == 9
        assert cpu.vf == 1

    # 8XY5
    def test_subtract_vy_from_vx(self, cpu):
        y = cpu.v0
        x = cpu.v1
        y.value = 10
        x.value = 10
        cpu(0x8105)
        assert y.value == 10
        assert x.value == 0
        assert cpu.vf == 0

    # 8XY5
    def test_subtract_vy_from_vx_borrow(self, cpu):
        y = cpu.v0
        x = cpu.v1
        y.value = 11
        x.value = 10
        cpu(0x8105)
        assert y.value == 11
        assert x.value == 255
        assert cpu.vf == 1

    # 8XY7
    def test_subtract_vx_from_vy(self, cpu):
        y = cpu.v0
        x = cpu.v1
        y.value = 10
        x.value = 10
        cpu(0x8107)
        assert y.value == 0
        assert x.value == 10
        assert cpu.vf.value == 0

    # 8XY7
    def test_subtract_vx_from_vy_borrow(self, cpu):
        y = cpu.v0
        x = cpu.v1
        y.value = 11
        x.value = 10
        cpu(0x8107)
        assert y.value == 255
        assert x.value == 10
        assert cpu.vf.value == 1

    # 8XY1
    def test_vx_or_vy(self, cpu):
        cpu.v0.value = 0b10101010
        cpu.v1.value = 0b01010101
        cpu(0x8101)
        assert cpu.v1.value == 0b11111111

    # 8XY2
    def test_vx_and_vy(self, cpu):
        cpu.v0.value = 0b10101110
        cpu.v1.value = 0b01010101
        cpu(0x8102)
        assert cpu.v1.value == 0b00000100

    # 8XY3
    def test_vx_xor_vy(self, cpu):
        cpu.v0.value = 0b10101110
        cpu.v1.value = 0b01010101
        cpu(0x8103)
        assert cpu.v1.value == 0b11111011

    # 8XY6
    def test_shift_right_sets_vf_to_lsb(self, cpu):
        y = cpu.v0

        y.value = 0b11100101
        cpu(0x8106)
        assert cpu.vf == 1

        y.value = 0b11100100
        cpu(0x8106)
        assert cpu.vf == 0

    # 8XY6
    def test_shift_right_stores_shifted_value_in_vx(self, cpu):
        y = cpu.v0
        x = cpu.v1

        y_value = 0b11100101
        y.value = y_value
        cpu(0x8106)
        assert x == 0b01110010
        assert y == y_value

    # 8XY6
    def test_shift_right_same_register(self, cpu):
        x = cpu.v0
        x.value = 0b11100011

        cpu(0x8006)
        assert x == 0b01110001
        cpu(0x8006)
        assert x == 0b00111000

    # 8XYE
    def test_shift_left_sets_vf_to_msb(self, cpu):
        y = cpu.v0

        y.value = 0b11100101
        cpu(0x810E)
        assert cpu.vf == 1

        y.value = 0b01100100
        cpu(0x810E)
        assert cpu.vf == 0

    # 8XYE
    def test_shift_left(self, cpu):
        y = cpu.v0
        x = cpu.v1
        y_value = 0b10001110
        y.value = y_value
        cpu(0x810E)
        assert x == 0b00011100
        assert y == y_value

        y_value = 0b00011100
        y.value = y_value
        cpu(0x810E)
        assert x == 0b00111000
        assert y == y_value

    # 8XYE
    def test_shift_left_same_register(self, cpu):
        x = cpu.v0
        x.value = 0b11100011
        cpu(0x800E)
        assert x == 0b11000110
        cpu(0x800E)
        assert x == 0b10001100

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
        cpu.v0.value = 0x23
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

    # 0NNN
    def test_exec_asm_not_implemented(self, cpu):
        with pytest.raises(NotImplementedError):
            cpu(0x0123)

    #3XNN
    def test_skip_vx_eq_nn__equal(self, cpu):
        cpu.v0.value = 0x33
        cpu(0x3033)
        assert cpu.pc == 0x204

    #3XNN
    def test_skip_vx_eq_nn__not_equal(self, cpu):
        cpu.v0.value = 0xff
        cpu(0x3033)
        assert cpu.pc == 0x202

    #5XY0
    def test_skip_vx_eq_vy__equal(self, cpu):
        cpu.v0.value = 0x33
        cpu.v1.value = 0x33
        cpu(0x5010)
        assert cpu.pc == 0x204

    #5XY0
    def test_skip_vx_eq_vy__not_equal(self, cpu):
        cpu.v0.value = 0x33
        cpu.v1.value = 0x66
        cpu(0x5010)
        assert cpu.pc == 0x202

    #4XNN
    def test_skip_vx_neq_nn__not_equal(self, cpu):
        cpu.v0.value = 0xff
        cpu(0x4033)
        assert cpu.pc == 0x204

    #4XNN
    def test_skip_vx_neq_nn__equal(self, cpu):
        cpu.v0.value = 0x33
        cpu(0x4033)
        assert cpu.pc == 0x202

    #9XY0
    def test_skip_vx_neq_vy__not_equal(self, cpu):
        cpu.v0.value = 0x33
        cpu.v1.value = 0x66
        cpu(0x9010)
        assert cpu.pc == 0x204

    #9XY0
    def test_skip_vx_neq_vy__equal(self, cpu):
        cpu.v0.value = 0x33
        cpu.v1.value = 0x33
        cpu(0x9010)
        assert cpu.pc == 0x202

    # FX15
    def test_set_delay_timer_to_vx(self, cpu):
        with freeze_time(NICE_DATE):
            cpu.v0.value = 0x12
            cpu(0xf015)
            assert cpu.delay_timer.value == 0x12

    # FX15
    def test_read_delay_timer_to_vx(self, cpu):
        with freeze_time(NICE_DATE):
            cpu.delay_timer.value = 0x12
            cpu(0xf007)
            assert cpu.v0 == 0x12

    # ANNN
    def test_store_nnn_in_i(self, cpu):
        cpu(0xA123)
        assert cpu.i.value == 0x123

    # FX1E
    def test_add_vx_to_i(self, cpu):
        cpu.i.value = 0x123
        cpu.v3.value = 2
        cpu(0xF31E)
        assert cpu.i.value == 0x125


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


class TestTimerRegister:

    @pytest.mark.parametrize(['initial_value', 'delta', 'expected'], (
            #One per second
            (10, 0, 10),
            (10, 1, 9),
            (10, 2, 8),
            (10, 3, 7),
            (10, 4, 6),
            (10, 5, 5),
            (10, 6, 4),
            (10, 7, 3),
            (10, 8, 2),
            (10, 9, 1),
            (10, 10, 0),
            (10, 11, 0), #Never below 0
            (10, 12, 0),
            (10, 1000000, 0),
            (0, 1000000, 0),
    ))
    def test_it_decrements_value_once_per_second(self, initial_value, delta, expected):
        t = TimerRegister()
        with freeze_time(NICE_DATE):
            t.value = initial_value
        with freeze_time(NICE_DATE + timedelta(seconds=delta)):
            assert t.value == expected