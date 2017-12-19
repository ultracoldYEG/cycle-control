from CycleControl.objects.hardware import *
from CycleControl.helpers import *


class Instruction(object):
    def __init__(self, hardware = HardwareSetup(), **kwargs):
        self._name = kwargs.get('name', '')
        self._duration = kwargs.get('duration', '0.0')
        self._stepsize = kwargs.get('stepsize', '0.0')

        self.digital_pins = {board.id: [False] * 24 for board in hardware.pulseblasters}
        self.analog_functions = {board.id: ['0.01'] * 8 for board in hardware.ni_boards}
        self.novatech_functions = {board.id: ['0'] * 12 for board in hardware.novatechs}

    def __eq__(self, other):
        attrs = ['name', 'duration', 'stepsize', 'digital_pins', 'analog_functions', 'novatech_functions']
        return all(getattr(self, attr, None) == getattr(other, attr, None) for attr in attrs)

    @property
    def name(self):
        return self._name

    @property
    def duration(self):
        return self._duration

    @property
    def stepsize(self):
        return self._stepsize

    @name.setter
    def name(self, name):
        try:
            self._name = str(name)
        except ValueError:
            pass

    @duration.setter
    def duration(self, duration):
        self._duration = duration


    @stepsize.setter
    def stepsize(self, stepsize):
        self._stepsize = stepsize


class DefaultSetup(Instruction):
    def __init__(self, hardware = HardwareSetup()):
        Instruction.__init__(self, hardware)
        self._name = 'Default'

    @property
    def name(self):
        return self._name

    @property
    def duration(self):
        return self._duration

    @property
    def stepsize(self):
        return self._stepsize

    @name.setter
    def name(self, name):
        pass

    @duration.setter
    def duration(self, duration):
        pass

    @stepsize.setter
    def stepsize(self, stepsize):
        pass


class StaticProcessVariable(object):
    PROPERTIES = ['name', 'default']
    def __init__(self, **kwargs):
        self._name = kwargs.get('name', '')
        self._default = kwargs.get('default', '0.0')

    def __eq__(self, other):
        return all(getattr(self, attr, None) == getattr(other, attr, None) for attr in self.PROPERTIES)

    def __getitem__(self, idx):
        return getattr(self, self.PROPERTIES[idx])

    def __setitem__(self, idx, val):
        setattr(self, self.PROPERTIES[idx], val)

    @property
    def name(self):
        return self._name

    @property
    def default(self):
        return self._default

    @name.setter
    def name(self, val):
        try:
            self._name = sterilize_string(val)
        except ValueError:
            pass

    @default.setter
    def default(self, default):
        try:
            float(default)
            self._default = default
        except ValueError:
            pass


class DynamicProcessVariable(StaticProcessVariable):
    PROPERTIES = ['name', 'default', 'start', 'end', 'logarithmic', 'send', ]

    def __init__(self, **kwargs):
        StaticProcessVariable.__init__(self, **kwargs)
        self._start = kwargs.get('start', '0.0')
        self._end = kwargs.get('end', '0.0')
        self._logarithmic = kwargs.get('logarithmic', False)
        self._send = kwargs.get('send', False)

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end

    @property
    def logarithmic(self):
        return self._logarithmic

    @property
    def send(self):
        return self._send

    @start.setter
    def start(self, start):
        try:
            float(start)
            self._start = start
        except ValueError:
            pass

    @end.setter
    def end(self, end):
        try:
            float(end)
            self._end = end
        except ValueError:
            pass

    @logarithmic.setter
    def logarithmic(self, state):
        try:
            self._logarithmic = bool(state)
        except ValueError:
            pass

    @send.setter
    def send(self, state):
        try:
            self._send = bool(state)
        except ValueError:
            pass

    def get_stepsize(self, steps):
        start = float(self.start)
        end = float(self.end)
        if steps > 1:
            steps -= 1
        if self.logarithmic:
            return pow(end / start, 1.0 / float(steps))
        return (end - start) / float(steps)
