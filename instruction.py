from cycle import *
from threading import Thread
from hardware_types import HardwareSetup

import time

class Procedure(object):
    def __init__(self, gui):
        self.parameters = ProcedureParameters()
        self.programmer = gui.programmer
        self.gui = gui
        self.current_step = 0
        self.activated = False
        self.run_lock = RunningLock()
        self.cycle_number = 0
        self.current_variables = {}

    def start_sequence(self):
        if len(self.parameters.instructions) <= 1:
            print('Put in more instructions')
            return
        with self.run_lock:
            self.current_step = 0
            while self.activated:
                if self.current_step < self.parameters.steps:
                    self.current_variables = self.parameters.get_cycle_variables(self.current_step)
                elif self.parameters.persistent:
                    self.current_variables = self.parameters.get_default_variables()
                else:
                    break
                cycle = Cycle(self.parameters.instructions, self.current_variables)
                self.run_cycle(cycle)
                time.sleep(self.parameters.delay)
                self.current_step += 1
                self.cycle_number += 1

    def run_cycle(self, cycle):
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

    def __eq__(self, other):
        if any(getattr(self, attr, None) != getattr(other, attr, None) for attr in ['steps', 'persistent', 'delay']):
            return False
        for attr in ['instructions', 'static_variables', 'dynamic_variables']:
            l1 = getattr(self, attr, None)
            l2 = getattr(other, attr, None)
            if len(l1) != len(l2):
                return False
            for i in range(len(l1)):
                if not l1[i] == l2[i]:
                    print l1[i]
                    print l2[i]
                    return False
        return True


    def save_to_file(self, fp, gui):
        dynamic_var_format = '{:>40}; {:>20}; {:>20}; {:>20}; {:>15}; {:>6}\n'
        static_var_format = '{:>40}; {:>20}\n'
        seq_param_format = '{:>10}; {:>11}; {:>8}\n'
        with open(fp, 'w+') as f:
            pulseblasters = [board.board_identifier for board in gui.hardware.pulseblasters]
            ni_boards = [board.board_identifier for board in gui.hardware.ni_boards]
            novatechs = [board.board_identifier for board in gui.hardware.novatechs]
            inst_format = '{{:>40}}; {{:>20}}; {{:>10}}; {{:>{digital_length}}}; {{:>{analog_length}}}; {{:>{novatech_length}}}\n'.format(**{
                'digital_length': str(30*len(pulseblasters)),
                'analog_length': str(70*len(ni_boards)),
                'novatech_length': str(70*len(novatechs))
            })
            f.write('INSTRUCTIONS\n')
            f.write(inst_format.format(
                'Name',
                'Duration',
                'Stepsize',
                'Digital Outputs'+''.join([', '+x for x in pulseblasters]),
                'Analog Outputs'+''.join([', '+x for x in ni_boards]),
                'Novatech Outputs'+''.join([', '+x for x in novatechs]),
            ))
            analog_format = '{} {} {} {} {} {} {} {}'
            novatech_format = '{} {} {} {} {} {} {} {} {} {} {} {}'
            for i in self.instructions:
                f.write(inst_format.format(
                    i.name,
                    i.duration,
                    i.stepsize,
                    ''.join([i.digital_pins.get(board) + ' \\ ' for board in pulseblasters])[:-3],
                    ''.join([analog_format.format(*i.analog_functions.get(board)) + ' \\ ' for board in ni_boards])[:-3],
                    ''.join([novatech_format.format(*i.novatech_functions.get(board)) + ' \\ ' for board in novatechs])[:-3]
                ))
            f.write('\nDYNAMIC_PROCESS_VARIABLES\n')
            f.write(dynamic_var_format.format(
                'Name',
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
            f.write('\nSTATIC_PROCESS_VARIABLES\n')
            f.write(static_var_format.format('Name', 'Value'))
            for i in self.static_variables:
                f.write(static_var_format.format(i.name, i.default))
            f.write('\nSEQUENCING_PARAMETERS\n')
            f.write(seq_param_format.format('Steps', 'Persistent', 'Delay'))
            f.write(seq_param_format.format(self.steps, int(self.persistent), self.delay))

    def load_from_file(self, fp, gui):
        self.instructions = []
        self.static_variables = []
        self.dynamic_variables = []
        self.steps = 1
        self.persistent = False
        self.delay = 0.0
        parsers = {
            "INSTRUCTIONS": self.parse_inst_line,
            "DYNAMIC_PROCESS_VARIABLES": self.parse_dyn_var_line,
            "STATIC_PROCESS_VARIABLES": self.parse_stat_var_line,
            "SEQUENCING_PARAMETERS": self.parse_seq_param_line,
        }
        with open(fp, 'rb') as f:
            for line in f:
                line = line.strip()
                if line in parsers:
                    parser = parsers.get(line)
                    parser(f, f.next(), gui)
                    continue

    def parse_inst_line(self, f, header, gui):
        header = [x.strip() for x in header.split(';')]

        pulseblasters = [x.strip() for x in header[3].split(',')][1:]
        ni_boards = [x.strip() for x in header[4].split(',')][1:]
        novatechs = [x.strip() for x in header[5].split(',')][1:]

        for line in f:
            if not line.strip():
                return
            line = [x.strip() for x in line.split(';')]
            inst = Instruction(gui.hardware)
            self.instructions.append(inst)

            inst.set_name(line[0])
            inst.set_duration(line[1])
            inst.set_stepsize(line[2])

            for i, board_inst in enumerate([x.strip() for x in line[3].split('\\')]):
                if pulseblasters[i] in inst.digital_pins:
                    inst.digital_pins.update([(pulseblasters[i], board_inst)])

            for i, board_inst in enumerate([x.strip() for x in line[4].split('\\')]):
                if ni_boards[i] in inst.analog_functions:
                    inst.analog_functions.update([(ni_boards[i], board_inst.split(' '))])

            for i, board_inst in enumerate([x.strip() for x in line[5].split('\\')]):
                if novatechs[i] in inst.novatech_functions:
                    inst.novatech_functions.update([(novatechs[i], board_inst.split(' '))])

    def parse_dyn_var_line(self, f, header, gui):
        for line in f:
            if not line.strip():
                return
            line = [x.strip() for x in line.split(';')]
            dyn_var = DynamicProcessVariable()
            self.dynamic_variables.append(dyn_var)

            dyn_var.set_name(line[0])
            dyn_var.set_start(line[1])
            dyn_var.set_end(line[2])
            dyn_var.set_default(line[3])
            dyn_var.set_log(int(line[4]))
            dyn_var.set_send(int(line[5]))

    def parse_stat_var_line(self, f, header, gui):
        for line in f:
            if not line.strip():
                return
            line = [x.strip() for x in line.split(';')]
            stat_var = StaticProcessVariable()
            self.static_variables.append(stat_var)

            stat_var.set_name(line[0])
            stat_var.set_default(line[1])

    def parse_seq_param_line(self, f, header, gui):
        for line in f:
            if not line.strip():
                return
            line = [x.strip() for x in line.split(';')]

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
    def __init__(self, hardware = HardwareSetup()):
        self.name = ''
        self.duration = 0.0
        self.stepsize = 0.0

        self.digital_pins = {board.board_identifier: '0' * 24 for board in hardware.pulseblasters}
        self.analog_functions = {board.board_identifier: ['0'] * 8 for board in hardware.ni_boards}
        self.novatech_functions = {board.board_identifier: ['0'] * 12 for board in hardware.novatechs}

    def __eq__(self, other):
        attrs = ['name', 'duration', 'stepsize', 'digital_pins', 'analog_functions', 'novatech_functions']
        return all(getattr(self, attr, None) == getattr(other, attr, None) for attr in attrs)

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
            if float(duration) >= 0.0:
                self.duration = duration
        except ValueError:
            pass

    def set_stepsize(self, stepsize):
        try:
            if float(stepsize) >= 0:
                self.stepsize = stepsize
        except ValueError:
            pass

    def set_analog_strings(self, string_list):
        self.analog_func_strings = string_list

class StaticProcessVariable(object):
    def __init__(self):
        self.name = ''
        self.default = '0.0'

    def __eq__(self, other):
        attrs = ['name', 'default']
        return all(getattr(self, attr, None) == getattr(other, attr, None) for attr in attrs)

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

    def __eq__(self, other):
        attrs = ['name', 'default', 'start', 'end', 'logarithmic', 'send', ]
        return all(getattr(self, attr, None) == getattr(other, attr, None) for attr in attrs)

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