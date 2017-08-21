from user_functions import *
import re
import copy

FUNCTION_REGEX = r'^(\w+)\((.*)\)$'
PULSE_WIDTH = 5e-6

def frange(x, y, jump):
    if jump == 0:
        jump = y
    result = []
    while x < y:
        result.append(x)
        x += jump
    return result

def replace_bit(bits, i, repl):
    return bits[:i] + repl + bits[i+1:]

def parse_function(string, variables):
    result = re.match(FUNCTION_REGEX, string)
    if result:
        key = result.group(1)
        args = [parse_arg(x.strip(), variables) for x in result.group(2).split(',')]
        if any([arg is None for arg in args]):
            print('Invalid function syntax: ', string)
            return None, None
        return key, args

    args = [parse_arg(string, variables)]
    if args:
        return 'const', args

    print('Invalid function syntax: ', string)
    return None, None

def parse_arg(arg, variables):
    if arg in variables:
        return variables.get(arg)
    try:
        arg = float(arg)
        return arg
    except ValueError:
        print('Couldnt parse argument ', arg)

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

    def create_analog_waveform(self):
        total_t = 0.0
        for inst in self.instructions:
            domain, waveforms = self.create_single_waveform(inst, inst.analog_functions)
            for i in domain:
                self.analog_domain.append(i + total_t)
            for board, channels in waveforms.iteritems():
                for channel in range(len(channels)):
                    self.analog_data.get(board)[channel] += waveforms.get(board)[channel]
            total_t += float(inst.duration)

    def create_novatech_waveform(self):
        total_t = 0.0
        for inst in self.instructions:
            domain, waveforms = self.create_single_waveform(inst, inst.novatech_functions)
            for i in domain:
                self.novatech_domain.append(i + total_t)
            for board, channels in waveforms.iteritems():
                for channel in range(len(channels)):
                    self.novatech_data.get(board)[channel] += waveforms.get(board)[channel]

            total_t += float(inst.duration)

    def create_digital_waveform(self):
        domain = [0.0]
        for inst in self.instructions:
            domain.append(domain[-1] + float(inst.duration))

        iter_pins = iter([inst.digital_pins for inst in self.instructions])
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

        duration = float(inst.duration)
        stepsize = float(inst.stepsize)

        if all((func == constFunc for board, board_funcs in funcs.iteritems() for func, args in board_funcs)):
            domain = [0.0]
        else:
            domain = frange(0.0, duration, stepsize)
            
        if self.instructions[-1] == inst:
            domain.append(duration)

        return domain, {board: [func(domain, duration, *args) for func, args in board_funcs] for board, board_funcs in funcs.iteritems()}
