from user_functions import *
import re

FUNCTION_REGEX = r'^(\w+)\((.*)\)$'
ANALOG_PIN = 2
NOVATECH_PIN = 3
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

def parse_function(string):
    result = re.match(FUNCTION_REGEX, string)
    if result:
        key = result.group(1)
        args = [float(x) for x in result.group(2).split(',')]
        return key, args
    try:
        args = [float(string)]
    except ValueError:
        print('not a valid function: ', string)
        return None, None
    return 'const', args

class Cycle(object):
    def __init__(self, instructions):
        self.instructions = instructions

        self.analog_domain = []
        self.novatech_domain = []
        self.digital_domain = []
        self.analog_data = [[] for  i in self.instructions[0].analog_functions]
        self.novatech_data = [[] for i in self.instructions[0].novatech_functions]
        self.digital_data = []

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
            for channel in range(len(waveforms)):
                self.analog_data[channel] += waveforms[channel]
            total_t += inst.duration

    def create_novatech_waveform(self):
        total_t = 0.0
        for inst in self.instructions:
            domain, waveforms = self.create_single_waveform(inst, inst.novatech_functions)
            for i in domain:
                self.novatech_domain.append(i + total_t)
            for channel in range(len(waveforms)):
                self.novatech_data[channel] += waveforms[channel]

            total_t += inst.duration

    def create_digital_waveform(self):
        domain = [0.0]
        for inst in self.instructions:
            domain.append(domain[-1] + inst.duration)

        iter_pins = iter([inst.digital_pins for inst in self.instructions])
        iter_domains = [iter(domain), iter(self.analog_domain), iter(self.novatech_domain)]
        next = [x.next() for x in iter_domains]

        while True:
            index = next.index(min(next))

            if index == 0:
                self.pulse_pins(min(next), iter_pins.next(), ANALOG_PIN, NOVATECH_PIN)
                next = [x.next() for x in iter_domains]
            elif index == 1:
                self.pulse_pins(min(next), self.digital_data[-1], ANALOG_PIN)
                next[1] = iter_domains[1].next()
            elif index == 2:
                self.pulse_pins(min(next), self.digital_data[-1], NOVATECH_PIN)
                next[2] = iter_domains[2].next()

            if min(next) == domain[-1]:
                self.digital_domain.append(min(next))
                self.digital_data.append(self.digital_data[-1])
                break

    def pulse_pins(self, domain, pin_flag, *pins):
        for pin in pins:
            pin_flag = replace_bit(pin_flag, pin, '1')

        self.digital_domain.append(domain)
        self.digital_data.append(pin_flag)

        for pin in pins:
            pin_flag = replace_bit(pin_flag, pin, '0')

        self.digital_domain.append(domain + PULSE_WIDTH)
        self.digital_data.append(pin_flag)

    def create_single_waveform(self, inst, func_strings):
        funcs = []
        for func_string in func_strings:
            key, args = parse_function(func_string)

            if key == 'const':
                funcs.append((constFunc, args))
            elif key == 'ramp':
                funcs.append((linFunc, args))
            elif key == 'sin':
               funcs.append((sinFunc, args))
            elif key == 'exp':
                funcs.append((expFunc, args))
            else:
                return

        duration = inst.duration
        stepsize = inst.stepsize

        if all((func == constFunc for func, args in funcs)):
            domain = [0.0]
        else:
            domain = frange(0.0, duration, stepsize)
            
        if self.instructions[-1] == inst:
            domain.append(duration)

        return domain, [func(domain, duration, *args) for func, args in funcs]