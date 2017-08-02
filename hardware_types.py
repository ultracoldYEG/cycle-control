class HardwareSetup(object):
    def __init__(self):
        self.pulseblasters = []
        self.ni_boards = []
        self.novatechs = []

class PulseBlasterBoard(object):
    def __init__(self):
        self.board_number = 0
        self.analog_pin = 23
        self.novatech_pin = 24

class NIBoard(object):
    def __init__(self):
        self.board_identifier = 'Dev0'
        self.channels = []
        self.min_voltage = -5.0
        self.max_voltage = 5.0

class VirtualNIChannel(object):
    def __init__(self, board, channel):
        self.board = board
        self.channel = channel
        self.enabled = False
        self.min = -1.0
        self.max = 1.0
        self.scaling = (1.0, 0.0)


class NovatechBoard(object):
    def __init__(self):
        self.com_port = 'COM0'