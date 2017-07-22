class Procedure(object):
    def __init__(self):
        self.instructions = []
        self.static_variables = []
        self.dynamic_variables = []

    def add_instruction(self, instruction):
        self.instructions.append()

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
        self.default = 0.0

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
        self.start = 0.0
        self.end = 0.0
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