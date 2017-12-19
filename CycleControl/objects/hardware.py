from collections import OrderedDict
import json

class HardwareSetup(object):
    def __init__(self, **kwargs):
        self.pulseblasters = kwargs.get('pulseblasters', [])
        self.ni_boards = kwargs.get('ni_boards', [])
        self.novatechs = kwargs.get('novatechs', [])

    def load_hardware_file(self, fp):
        self.pulseblasters = []
        self.ni_boards = []
        self.novatechs = []

        with open(fp, 'rb') as f:
            context = json.load(f)

        for board in context.get('pulseblasters'):
            pb = PulseBlasterBoard(board.get('id'))
            pb.analog_pin = board.get('analog_pin')
            pb.novatech_pin = board.get('novatech_pin')
            for i, channel in enumerate(board.get('channels')):
                pb[i].enabled = channel.get('enabled')
            self.pulseblasters.append(pb)

        for board in context.get('ni_boards'):
            ni_board = NIBoard(board.get('id'))
            for i, channel in enumerate(board.get('channels')):
                ni_board[i].enabled = channel.get('enabled')
                ni_board[i].label = channel.get('label')
                ni_board[i].min = channel.get('min')
                ni_board[i].max = channel.get('max')
                ni_board[i].scaling = channel.get('scaling')
            self.ni_boards.append(ni_board)

        for board in context.get('novatechs'):
            novatech = NovatechBoard(board.get('id'))
            for i, channel in enumerate(board.get('channels')):
                novatech[i].enabled = channel.get('enabled')
            self.novatechs.append(novatech)

    def serialize_board(self, board, board_params = (), channel_params = ()):
        serialized_board = OrderedDict([(attr, getattr(board, attr)) for attr in board_params])
        channels = []
        for channel in board:
            channels.append(OrderedDict([(attr, getattr(channel, attr)) for attr in channel_params]))
        serialized_board.update([('channels', channels)])
        return serialized_board

    def save_hardware_file(self, fp):
        pulseblasters = []
        for board in self.pulseblasters:
            serialized_board = self.serialize_board(
                board,
                board_params = ['id', 'analog_pin', 'novatech_pin'],
                channel_params = ['enabled']
            )
            pulseblasters.append(serialized_board)

        ni_boards = []
        for board in self.ni_boards:
            serialized_board = self.serialize_board(
                board,
                board_params = ['id'],
                channel_params = ['enabled', 'label', 'min', 'max', 'scaling']
            )
            ni_boards.append(serialized_board)

        novatechs = []
        for board in self.novatechs:
            serialized_board = self.serialize_board(
                board,
                board_params = ['id'],
                channel_params = ['enabled']
            )
            novatechs.append(serialized_board)

        with open(fp, 'w+') as f:
            json.dump(OrderedDict([
                ('pulseblasters', pulseblasters),
                ('ni_boards', ni_boards),
                ('novatechs', novatechs),
            ]), f, indent=2)


class Board (object):
    def __init__(self, id):
        self.id = id
        self.channels = []

    def __getitem__(self, idx):
        return self.channels[idx]

    def num_active(self):
        return sum([1 for channel in self.channels if channel.enabled])


class Channel(object):
    def __init__(self):
        self.enabled = False


class PulseBlasterBoard(Board):
    def __init__(self, num):
        super(PulseBlasterBoard, self).__init__(num)
        self.analog_pin = None
        self.novatech_pin = None
        self.channels = [PulseBlasterChannel() for x in range(24)]


class PulseBlasterChannel(Channel):
    def __init__(self):
        super(PulseBlasterChannel, self).__init__()


class NIBoard(Board):
    def __init__(self, id):
        super(NIBoard, self).__init__(id)
        self.channels = [VirtualNIChannel() for x in range(8)]


class VirtualNIChannel(Channel):
    def __init__(self):
        super(VirtualNIChannel, self).__init__()
        self.label = ''
        self.min = -1.0
        self.max = 1.0
        self.scaling = ''


class NovatechBoard(Board):
    def __init__(self, port):
        super(NovatechBoard, self).__init__(port)
        self.channels = [NovatechChannel() for x in range(4)]

    def num_active(self):
        result = super(NovatechBoard, self).num_active()
        return result * 3

class NovatechChannel(Channel):
    def __init__(self):
        super(NovatechChannel, self).__init__()