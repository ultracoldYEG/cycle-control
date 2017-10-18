class HardwareSetup(object):
    def __init__(self):
        self.pulseblasters = []
        self.ni_boards = []
        self.novatechs = []

    def load_hardware_file(self, fp):
        self.pulseblasters = []
        self.ni_boards = []
        self.novatechs = []
        parsers = {
            "PULSEBLASTER": self.parse_pb,
            "NI BOARD": self.parse_ni,
            "NOVATECH": self.parse_nova
        }
        with open(fp, 'r') as f:
            for line in f:
                line = [x.strip() for x in line.split(';')]
                if line[0] in parsers:
                    f.next()
                    parser = parsers.get(line[0])
                    parser(f, line[1])
                    continue

    def parse_pb(self, f, num):
        pb = PulseBlasterBoard(str(num))
        self.pulseblasters.append(pb)
        for line in f:
            if not line.strip():
                return
            line = [x.strip() for x in line.split(';')]
            channel = pb.channels[int(line[0])]
            channel.enabled = bool(int(line[1]))

    def parse_ni(self, f, id):
        ni = NIBoard(str(id))
        self.ni_boards.append(ni)
        for line in f:
            if not line.strip():
                return
            line = [x.strip() for x in line.split(';')]
            channel = ni.channels[int(line[0])]
            channel.enabled = bool(int(line[1]))
            channel.label = line[2]
            channel.min = float(line[3])
            channel.max = float(line[4])
            channel.scaling = str(line[5])

    def parse_nova(self, f, port):
        nova = NovatechBoard(str(port))
        self.novatechs.append(nova)
        for line in f:
            if not line.strip():
                return
            line = [x.strip() for x in line.split(';')]
            channel = nova.channels[int(line[0])]
            channel.enabled = bool(int(line[1]))

    def save_hardware_file(self, fp):
        with open(fp, 'w+') as f:
            pb_format = ' {:>8}; {:>8}\n'
            ni_format = ' {:>8}; {:>8}; {:>30}; {:>8}; {:>8}; {:>20}\n'
            nova_format = ' {:>8}; {:>8}\n'

            for board in self.pulseblasters:
                f.write('\nPULSEBLASTER; {0}\n'.format(board.board_identifier))
                f.write(pb_format.format('Channel', 'Enabled'))
                for i, channel in enumerate(board.channels):
                    f.write(pb_format.format(i, int(channel.enabled)))

            for board in self.ni_boards:
                f.write('\nNI BOARD; {0}\n'.format(board.board_identifier))
                f.write(ni_format.format('Channel', 'Enabled', 'Label', 'Min', 'Max', 'Scaling Params'))
                for i, channel in enumerate(board.channels):
                    f.write(ni_format.format(
                        i,
                        int(channel.enabled),
                        channel.label,
                        channel.min,
                        channel.max,
                        channel.scaling
                    ))

            for board in self.novatechs:
                f.write('\nNOVATECH; {0}\n'.format(board.board_identifier))
                f.write(nova_format.format('Channel', 'Enabled'))
                for i, channel in enumerate(board.channels):
                    f.write(nova_format.format(i, int(channel.enabled)))


class Board (object):
    def __init__(self, id):
        self.board_identifier = id
        self.channels = []


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
        self.enabled = False


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


class NovatechChannel(Channel):
    def __init__(self):
        super(NovatechChannel, self).__init__()