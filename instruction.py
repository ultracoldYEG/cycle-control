from cycle import *

class Procedure(object):
    def __init__(self, programmer):
        self.instructions = []
        self.static_variables = []
        self.dynamic_variables = []
        self.programmer = programmer
        self.steps = 1

    def start_sequence(self):
        if len(self.instructions) <= 1:
            print('Put in more instructions')
            return
        variables = {x.name: float(x.default) for x in self.static_variables}
        for var in self.dynamic_variables:
            variables[var.name] = None
        for i in range(self.steps):
            for var in self.dynamic_variables:
                variables[var.name] = self.get_dynamic_variable_value(i, var)
            cycle = Cycle(self.instructions, variables)
            self.programmer.program_device_handler(cycle)
            self.programmer.start_device_handler()

    def get_dynamic_variable_value(self, step, dyn_var):
        start = float(dyn_var.start)
        end = float(dyn_var.end)
        step = float(step)
        if dyn_var.logarithmic:
            steps = self.steps
            if self.steps > 1:
                steps -= 1
            return start * pow(end/start, float(step)/float(steps))
        return start + (end - start) * step/float(self.steps)

    def get_save_info(self):
        result = ''
        inst_format = '{:>40}; {:>20}; {:>10}; {:>26}; {:>75}; {:>75}\n'
        dynamic_var_format = '{:>40}; {:>20}; {:>20}; {:>20}; {:>15}; {:>6}\n'
        static_var_format = '{:>40}; {:>20}\n'
        result += (inst_format.format(
            '===Instructions===       Name',
            'Duration',
            'Stepsize',
            'Digital Pins',
            'Analog Outputs',
            'Novatech Outputs'
        ))
        for i in self.instructions:
            result += (inst_format.format(
                i.name,
                i.duration,
                i.stepsize,
                i.digital_pins,
                ''.join([x + ' ' for x in i.analog_functions]),
                ''.join([x + ' ' for x in i.novatech_functions])
            ))
        result += ('\n')
        result += (dynamic_var_format.format(
            '===Dynamic Process Variables===    Name',
            'Start',
            'End',
            'Default',
            'Logarithmic',
            'Send'
        ))
        for i in self.dynamic_variables:
            result += (dynamic_var_format.format(
                i.name,
                i.start,
                i.end,
                i.default,
                int(i.logarithmic),
                int(i.send)
            ))
        result += ('\n')
        result += (static_var_format.format(
            '===Static Process Variables===    Name',
            'Value'
        ))
        for i in self.static_variables:
            result += (static_var_format.format(
                i.name,
                i.default,
            ))
        return result


class Instruction(object):
    # this will contain all the information in a single instruction (a single row in the program)
    def __init__(self):
        self.name = ''
        self.duration = 0.0
        self.stepsize = 0.0

        self.digital_pins = '0' * 24
        self.analog_functions = ['0'] * 8
        self.novatech_functions = ['0'] * 12


    def set_digital_pins(self, flag_string):
        try:
            self.digital_pins = str(flag_string)
        except ValueError:
            pass

    def set_name(self, name):
        try:
            self.name = str(name)
        except ValueError:
            pass

    def set_duration(self, duration):
        try:
            float(duration)
            self.duration = duration
        except ValueError:
            pass

    def set_stepsize(self, stepsize):
        try:
            float(stepsize)
            self.stepsize = stepsize
        except ValueError:
            pass

    def set_analog_strings(self, string_list):
        self.analog_func_strings = string_list

class StaticProcessVariable(object):
    def __init__(self):
        self.name = ''
        self.default = '0.0'

    def set_name(self, name):
        try:
            self.name = str(name)
        except ValueError:
            pass

    def set_default(self, default):
        try:
            float(default)
            self.default = default
        except ValueError:
            pass

class DynamicProcessVariable(StaticProcessVariable):
    def __init__(self):
        super(DynamicProcessVariable, self).__init__()
        self.start = '0.0'
        self.end = '0.0'
        self.logarithmic = False
        self.send = False

    def set_start(self, start):
        try:
            float(start)
            self.start = start
        except ValueError:
            pass

    def set_end(self, end):
        try:
            float(end)
            self.end = end
        except ValueError:
            pass

    def set_log(self, state):
        try:
            self.logarithmic = bool(state)
        except ValueError:
            pass

    def set_send(self, state):
        try:
            self.send = bool(state)
        except ValueError:
            pass