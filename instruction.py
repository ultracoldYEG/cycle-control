from cycle import *
from threading import Thread

import time

class Procedure(object):
    def __init__(self, programmer, gui):
        self.parameters = ProcedureParameters()
        self.programmer = programmer
        self.gui = gui
        self.current_step = 0
        self.activated = False
        self.run_lock = RunningLock()
        self.cycle_number = 0

    def start_sequence(self):
        instructions = self.parameters.instructions
        steps = self.parameters.steps
        with self.run_lock:
            if len(instructions) <= 1:
                print('Put in more instructions')
                return
            self.current_step = 0
            while self.activated:
                self.current_step += 1
                self.cycle_number += 1
                if self.current_step <= steps:
                    variables = self.parameters.get_cycle_variables(self.current_step - 1)
                    self.gui.update_current_dyn_vars(self.parameters.get_dynamic_variables(self.current_step - 1))
                    cycle = Cycle(instructions, variables)
                    self.start_cycle(cycle)
                elif self.parameters.persistent:
                    variables = self.parameters.get_default_variables()
                    cycle = Cycle(instructions, variables)
                    self.start_cycle(cycle)
                else:
                    break
                time.sleep(self.parameters.delay)

    def start_cycle(self, cycle):
        thread = cycle_thread(self.programmer, cycle)
        self.gui.worker.procedure = self
        self.gui.worker.start()
        thread.start()
        thread.join()


class ProcedureParameters(object):
    def __init__(self):
        self.instructions = []
        self.static_variables = []
        self.dynamic_variables = []
        self.steps = 1
        self.persistent = False
        self.delay = 0.0

    def save_to_file(self, fp):
        inst_format = '{:>40}; {:>20}; {:>10}; {:>26}; {:>75}; {:>75}\n'
        dynamic_var_format = '{:>40}; {:>20}; {:>20}; {:>20}; {:>15}; {:>6}\n'
        static_var_format = '{:>40}; {:>20}\n'
        seq_param_format = '{:>40}; {:>11}; {:>8}\n'
        with open(fp, 'w+') as f:
            f.write(inst_format.format(
                '===Instructions===       Name',
                'Duration',
                'Stepsize',
                'Digital Pins',
                'Analog Outputs',
                'Novatech Outputs'
            ))
            for i in self.instructions:
                f.write(inst_format.format(
                    i.name,
                    i.duration,
                    i.stepsize,
                    i.digital_pins,
                    ''.join([x + ' ' for x in i.analog_functions]),
                    ''.join([x + ' ' for x in i.novatech_functions])
                ))
            f.write('\n')
            f.write(dynamic_var_format.format(
                '===Dynamic Process Variables===    Name',
                'Start',
                'End',
                'Default',
                'Logarithmic',
                'Send'
            ))
            for i in self.dynamic_variables:
                f.write(dynamic_var_format.format(
                    i.name,
                    i.start,
                    i.end,
                    i.default,
                    int(i.logarithmic),
                    int(i.send)
                ))
            f.write('\n')
            f.write(static_var_format.format('===Static Process Variables===    Name', 'Value'))
            for i in self.static_variables:
                f.write(static_var_format.format(i.name, i.default))
            f.write('\n')
            f.write(seq_param_format.format('===Sequencing Parameters===    Steps', 'Persistent', 'Delay'))
            f.write(seq_param_format.format(self.steps, int(self.persistent), self.delay))

    def load_from_file(self, fp):
        parsers = iter([
            self.parse_inst_line,
            self.parse_dyn_var_line,
            self.parse_stat_var_line,
            self.parse_seq_param_line
        ])
        parser = parsers.next()
        with open(fp, 'rb') as f:
            self.instructions = []
            self.static_variables = []
            self.dynamic_variables = []
            self.steps = 1
            self.persistent = False
            self.delay = 0.0
            f.next()
            for line in f:
                line = [x.strip() for x in line.split(';')]
                if line == ['']:
                    f.next()
                    parser = parsers.next()
                    continue

                parser(line)

    def parse_inst_line(self, line):
        inst = Instruction()
        inst.set_name(line[0])
        inst.set_duration(line[1])
        inst.set_stepsize(line[2])
        inst.set_digital_pins(line[3])
        inst.analog_functions = line[4].split(' ')
        inst.novatech_functions = line[5].split(' ')

        self.instructions.append(inst)

    def parse_dyn_var_line(self, line):
        dyn_var = DynamicProcessVariable()
        dyn_var.set_name(line[0])
        dyn_var.set_start(line[1])
        dyn_var.set_end(line[2])
        dyn_var.set_default(line[3])
        dyn_var.set_log(int(line[4]))
        dyn_var.set_send(int(line[5]))

        self.dynamic_variables.append(dyn_var)

    def parse_stat_var_line(self, line):
        stat_var = StaticProcessVariable()
        stat_var.set_name(line[0])
        stat_var.set_default(line[1])

        self.static_variables.append(stat_var)

    def parse_seq_param_line(self, line):

        self.steps = int(line[0])
        self.persistent = bool(int(line[1]))
        self.delay = float(line[2])

    def get_static_variables(self):
        return {x.name: float(x.default) for x in self.static_variables}

    def get_dynamic_variables(self, step):
        return {x.name: self.get_dynamic_variable_value(step, x) for x in self.dynamic_variables if x.send}

    def get_dynamic_default_variables(self):
        return {x.name: float(x.default) for x in self.dynamic_variables}

    def get_cycle_variables(self, step):
        variables = self.get_static_variables()
        variables.update(self.get_dynamic_variables(step))
        return variables

    def get_default_variables(self):
        variables = self.get_static_variables()
        variables.update(self.get_dynamic_default_variables())
        return variables

    def get_dynamic_variable_value(self, step, dyn_var):
        start = float(dyn_var.start)
        stepsize = dyn_var.get_stepsize(self.steps)
        if dyn_var.logarithmic:
            return start * pow(stepsize, float(step))
        return start + stepsize * step

    def get_total_time(self):
        return sum([float(x.duration) for x in self.instructions])

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

    def get_stepsize(self, steps):
        start = float(self.start)
        end = float(self.end)
        if steps > 1:
            steps -= 1
        if self.logarithmic:
            return pow(end / start, 1.0 / float(steps))
        return (end - start) / float(steps)\


class cycle_thread(Thread):
    def __init__(self, programmer, cycle):
        Thread.__init__(self)
        self.programmer = programmer
        self.cycle = cycle

    def run(self):
        self.programmer.program_device_handler(self.cycle)
        self.programmer.start_device_handler()
        print('Cycle complete. Waiting for next start command..')

class RunningLock(object):
    def __init__(self):
        self.running = False

    def __enter__(self):
        self.running = True

    def __exit__(self, *args):
        self.running = False