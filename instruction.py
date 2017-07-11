class Instruction():
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
            self.duration = float(duration)
        except ValueError:
            pass

    def set_stepsize(self, stepsize):
        try:
            self.stepsize = float(stepsize)
        except ValueError:
            pass

    def set_analog_strings(self, string_list):
        self.analog_func_strings = string_list
