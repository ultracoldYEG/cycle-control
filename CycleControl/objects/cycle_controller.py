from CycleControl.objects.procedure import *
from CycleControl.objects.programmer import *


class Controller(object):
    def __init__(self, **kwargs):
        self.hardware = HardwareSetup(**kwargs)
        self.default_setup = DefaultSetup(self.hardware)
        self.programmer = Programmer(self)
        self.procedure = Procedure(self)
        self.proc_params = ProcedureParameters(**kwargs)

        self.clipboard = None