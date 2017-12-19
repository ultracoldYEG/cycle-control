from CycleControl.objects.cycle import *
from CycleControl.objects.instruction import *

from threading import Thread
from collections import OrderedDict

import json
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
        if len(self.parameters.instructions) < 1:
            print('Put in more instructions')
            return
        with self.run_lock:
            self.current_step = 0
            while self.activated:
                if self.current_step >= self.parameters.steps and not self.parameters.persistent:
                    break
                self.current_variables = self.parameters.get_cycle_variables(self.current_step)
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
        self.gui.worker.wait()


class ProcedureParameters(object):
    def __init__(self, **kwargs):
        self.instructions = kwargs.get('instructions', [])
        self.static_variables = kwargs.get('static_variables', [])
        self.dynamic_variables = kwargs.get('dynamic_variables', [])
        self.steps = kwargs.get('steps', 1)
        self.persistent = kwargs.get('persistent', False)
        self.delay = kwargs.get('delay', 0.0)

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
                    return False
        return True

    def save_to_file(self, fp, gui):
        instructions = []
        for inst in self.instructions:
            instructions.append( OrderedDict([(attr, getattr(inst, attr)) for attr in [
                'name',
                'duration',
                'stepsize',
                'digital_pins',
                'analog_functions',
                'novatech_functions'
            ]] ))

        dynamic_variables = []
        for var in self.dynamic_variables:
            dynamic_variables.append( OrderedDict([(attr, getattr(var, attr)) for attr in [
                'name',
                'start',
                'end',
                'default',
                'logarithmic',
                'send'
            ]] ))

        static_variables = []
        for var in self.static_variables:
            static_variables.append( OrderedDict([(attr, getattr(var, attr)) for attr in [
                'name',
                'default',
            ]] ))

        sequencing_parameters = OrderedDict([
            ('steps', self.steps),
            ('persistent', self.persistent),
            ('delay', self.delay),
       ])

        with open(fp, 'w+') as f:
            json.dump(OrderedDict([
                ('sequencing_parameters', sequencing_parameters),
                ('dynamic_variables', dynamic_variables),
                ('static_variables', static_variables),
                ('instructions', instructions),
            ]), f, indent = 2)

    def load_from_file(self, fp, gui):
        self.instructions = []
        self.static_variables = []
        self.dynamic_variables = []
        self.steps = 1
        self.persistent = False
        self.delay = 0.0

        with open(fp, 'rb') as f:
            context = json.load(f)

        for inst in context.get('instructions'):
            i = Instruction(gui.hardware)
            i.set_name(inst.get('name'))
            i.set_duration(inst.get('duration'))
            i.set_stepsize(inst.get('stepsize'))
            i.digital_pins.update(inst.get('digital_pins'))
            i.analog_functions.update(inst.get('analog_functions'))
            i.novatech_functions.update(inst.get('novatech_functions'))
            self.instructions.append(i)

        for var in context.get('dynamic_variables'):
            dyn_var = DynamicProcessVariable()
            dyn_var.set_name(var.get('name'))
            dyn_var.set_start(var.get('start'))
            dyn_var.set_end(var.get('end'))
            dyn_var.set_default(var.get('default'))
            dyn_var.set_log(var.get('logarithmic'))
            dyn_var.set_send(var.get('send'))
            self.dynamic_variables.append(dyn_var)

        for var in context.get('static_variables'):
            stat_var = StaticProcessVariable()
            stat_var.set_name(var.get('name'))
            stat_var.set_default(var.get('default'))
            self.static_variables.append(stat_var)

        params = context.get('sequencing_parameters')
        self.steps = params.get('steps')
        self.persistent = params.get('persistent')
        self.delay = params.get('delay')

    def get_static_variables(self):
        return {x.name: float(x.default) for x in self.static_variables}

    def get_dynamic_variables(self, step):
        return {x.name: (self.get_dynamic_variable_value(step, x) if x.send else x.default) for x in self.dynamic_variables}

    def get_dynamic_default_variables(self):
        return {x.name: float(x.default) for x in self.dynamic_variables}

    def get_cycle_variables(self, step):
        variables = self.get_static_variables()
        dynamic_variables = self.get_dynamic_variables(step) if step < self.steps else self.get_dynamic_default_variables()
        variables.update(dynamic_variables)
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
        vars = self.get_default_variables()
        return sum([parse_arg(x.duration, vars) for x in self.instructions])



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