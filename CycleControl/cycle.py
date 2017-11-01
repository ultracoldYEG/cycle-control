from user_functions import *
from helpers import *
import copy

PULSE_WIDTH = 5e-6

class Cycle(object):
    def __init__(self, instructions, variables):
        self.instructions = [x for x in instructions if parse_arg(x.duration, variables) > 0.0]
        self.variables = variables

        self.analog_domain = []
        self.novatech_domain = []
        self.digital_domain = []
        self.analog_data = {board: [[] for i in vals] for board, vals in self.instructions[0].analog_functions.iteritems()}
        self.novatech_data = {board: [[] for i in vals] for board, vals in self.instructions[0].novatech_functions.iteritems()}
        self.digital_data = {board: [] for board, vals in self.instructions[0].digital_pins.iteritems()}

    def create_waveforms(self):
        self.create_analog_waveform()
        self.create_novatech_waveform()
        self.create_digital_waveform()
        self.domain_check()

    def domain_check(self):
        for i, val in enumerate(self.digital_domain[:-1]):
            if abs(val - self.digital_domain[i + 1]) < 10 ** -6:
                raise ValueError, ('value error in domain', i, val, self.digital_domain[i + 1])

    def create_analog_waveform(self):
        total_t = 0.0
        for inst in self.instructions:
            domain, waveforms = self.create_single_waveform(inst, inst.analog_functions)
            for i in domain:
                self.analog_domain.append(i + total_t)
            for board, channels in waveforms.iteritems():
                for channel in range(len(channels)):
                    self.analog_data.get(board)[channel] += waveforms.get(board)[channel]
            total_t += parse_arg(inst.duration, self.variables)

    def create_novatech_waveform(self):
        total_t = 0.0
        for inst in self.instructions:
            domain, waveforms = self.create_single_waveform(inst, inst.novatech_functions)
            for i in domain:
                self.novatech_domain.append(i + total_t)
            for board, channels in waveforms.iteritems():
                for channel in range(len(channels)):
                    self.novatech_data.get(board)[channel] += waveforms.get(board)[channel]

            total_t += parse_arg(inst.duration, self.variables)

    def create_digital_waveform(self):
        domain = [0.0]
        for inst in self.instructions:
            domain.append(domain[-1] + parse_arg(inst.duration, self.variables))

        iter_pins = iter([copy.copy(inst.digital_pins) for inst in self.instructions])
        iter_domains = [iter(domain), iter(self.analog_domain), iter(self.novatech_domain)]
        next = [x.next() for x in iter_domains]

        # TODO include option to select which analog/novatech pins are used
        ANALOG_PINS = [('0', 2)]
        NOVATECH_PINS = [('0', 3)]

        while True:
            index = next.index(min(next))

            if index == 0:
                current_pins = iter_pins.next()
                self.pulse_pins(min(next), current_pins, *ANALOG_PINS + NOVATECH_PINS)
                next = [x.next() for x in iter_domains]

            elif index == 1:
                self.pulse_pins(min(next), current_pins, *ANALOG_PINS)
                next[1] = iter_domains[1].next()
            elif index == 2:
                self.pulse_pins(min(next), current_pins, *NOVATECH_PINS)
                next[2] = iter_domains[2].next()

            if min(next) == domain[-1]:
                self.digital_domain.append(min(next))
                for board, data in current_pins.iteritems():
                    self.digital_data.get(board).append(data)
                break

    def pulse_pins(self, domain, all_pins, *pins):
        for item in pins:
            board = item[0]
            pin = item[1]
            board_pins = all_pins.get(board)
            board_pins = replace_bit(board_pins, pin, '1')
            all_pins.update([(board, board_pins)])

        self.digital_domain.append(domain)
        for board, data in all_pins.iteritems():
            self.digital_data.get(board).append(data)

        for item in pins:
            board = item[0]
            pin = item[1]
            board_pins = all_pins.get(board)
            board_pins = replace_bit(board_pins, pin, '0')
            all_pins.update([(board, board_pins)])

        self.digital_domain.append(domain + PULSE_WIDTH)
        for board, data in all_pins.iteritems():
            self.digital_data.get(board).append(data)

    def create_single_waveform(self, inst, boards):
        functions = self.get_functions(boards)
        duration = parse_arg(inst.duration, self.variables)
        stepsize = parse_arg(inst.stepsize, self.variables)

        if all((func == constFunc for board, board_funcs in functions.iteritems() for func, args in board_funcs)):
            domain = [0.0]
        else:
            domain = range(0, int(duration * 10 ** 12),  int(stepsize * 10 ** 12))

        if duration * 10 ** 12 - domain[-1] < stepsize * 10 ** 12 and len(domain) > 2:
            del domain[-1]

        if id(self.instructions[-1]) == id(inst):
            domain.append(int(duration * 10 ** 12))

        domain = [float(x) / 10 ** 12 for x in domain]
        return domain, {board: [func(domain, duration, *args) for func, args in board_funcs] for board, board_funcs in functions.iteritems()}

    def get_functions(self, boards):
        funcs = {}
        for board, func_strings in boards.iteritems():
            board_funcs = []
            funcs.update([[board, board_funcs]])
            for func_string in func_strings:
                key, args = parse_function(func_string, self.variables)

                if key in FUNCTION_MAP:
                    func = FUNCTION_MAP.get(key)
                    board_funcs.append((func, args))
                else:
                    print key, 'is not a valid function key'
                    return
        return funcs
