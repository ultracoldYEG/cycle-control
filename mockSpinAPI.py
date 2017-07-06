PULSE_PROGRAM = 0
FREQ_REGS = 1

class MockSpinAPI(object):
    def __init__(self):
        self.selected_board = -1
        self.debug = False
        self.clock = 100.0
        self.activated = False
        self.programming = False
        self.instructions = []

    def pb_set_debug(self, debug):
        self.debug = debug
        return self.debug

    def pb_get_version(self):
        return 'mock version'

    def pb_count_boards(self):
        return 1

    def pb_select_board(self, board_number):
        self.selected_board = board_number
        return self.selected_board

    def pb_init(self):
        return 0

    def pb_core_clock(self, rate):
        self.clock = rate
        return self.clock

    def pb_start(self):
        if self.programming:
            print 'ERROR pb is programming'
            return
        self.activated = True
        print('Pulse plaster activated')


    def pb_stop(self):
        self.activated = False
        print('Pulse plaster stopped')

    def pb_start_programming(self, target):
        if target != 0:
            print 'Bad target'
            return
        if self.activated:
            print 'ERROR pb is activated'
            return
        self.programming = True
        self.instructions = []
        print('Pulse plaster programming activated')

    def pb_stop_programming(self):
        self.programming = False
        print('Pulse plaster programming stopped')

    def pb_inst_pbonly(self, args):
        self.instructions.append(args)
        return self.instructions[-1]

    def pb_close(self):
        self.pb_stop()
        self.pb_stop_programming()
        print('Pulse blaster closed')


spinapi = MockSpinAPI()


ns = 1.0
us = 1000.0
ms = 1000000.0
s  = 1000000000.0

MHz = 1.0
kHz = 0.001
Hz = 0.000001

def enum(**enums):
    return type('Enum', (), enums)

# Instruction enum
Inst = enum(
    CONTINUE=0,
    STOP=1,
    LOOP=2,
    END_LOOP=3,
    JSR=4,
    RTS=5,
    BRANCH=6,
    LONG_DELAY=7,
    WAIT=8,
    RTI=9
)


def pb_get_version():
    return spinapi.pb_get_version()

def pb_count_boards():
    return spinapi.pb_count_boards()


def pb_init():
    return spinapi.pb_init()


def pb_set_debug(debug):
    return spinapi.pb_set_debug(debug)


def pb_select_board(board_number):
    return spinapi.pb_select_board(board_number)


def pb_core_clock(clock):
    return spinapi.pb_core_clock(clock)


def pb_start_programming(target):
    return spinapi.pb_start_programming(target)


def pb_stop_programming():
    return spinapi.pb_stop_programming()


def pb_inst_pbonly(*args):
    t = list(args)
    # Argument 3 must be a double
    args = tuple(t)
    return spinapi.pb_inst_pbonly(args)


def pb_start():
    return spinapi.pb_start()


def pb_stop():
    return spinapi.pb_stop()

def pb_close():
    return spinapi.pb_close()