import unittest

import os

import CycleControl.cycle as cycle_objects
import CycleControl.instruction as instruction_objects
import CycleControl.hardware_types as hardware_types

class MockGui(object):
    def __init__(self, hardware = hardware_types.HardwareSetup()):
        self.hardware = hardware

class TestCycleBaseCase(unittest.TestCase):
    def setUp(self):
        hardware = hardware_types.HardwareSetup()
        procedure_params = instruction_objects.ProcedureParameters()
        gui = MockGui(hardware = hardware)

        hardware.load_hardware_file(os.path.join(os.getcwd(), 'tests', 'test_hardware.txt'))
        procedure_params.load_from_file(os.path.join(os.getcwd(), 'tests', 'test_procedure.txt'), gui)

        self.cycle = cycle_objects.Cycle(
            procedure_params.instructions,
            procedure_params.get_default_variables()
        )

    def assertFloatListEqual(self, obj1, obj2):
        tolerance = 10e-9 # 10 nanoseconds
        for item1, item2 in zip(obj1, obj2):
            if abs(item1 - item2) > tolerance:
                self.fail('{0} and {1} are not within tolerance'.format(item1, item2))

class TestCycleCreation(TestCycleBaseCase):
    def testCreation(self):
        hardware = hardware_types.HardwareSetup(
            pulseblasters=[hardware_types.PulseBlasterBoard(0)],
            ni_boards=[hardware_types.NIBoard('Dev0')],
            novatechs=[hardware_types.NovatechBoard('COM1')],
        )
        instructions = [instruction_objects.Instruction(hardware)]
        instructions[0].set_duration('1.0')
        cycle = cycle_objects.Cycle(instructions, {'var1': 500})
        self.assertDictEqual({'var1': 500}, cycle.variables)

        self.assertEqual([], cycle.analog_domain)
        self.assertEqual([], cycle.novatech_domain)
        self.assertEqual([], cycle.digital_domain)

        self.assertEqual({'Dev0': [[]] * 8}, cycle.analog_data)
        self.assertEqual({'COM1': [[]] * 12}, cycle.novatech_data)
        self.assertEqual({0: [] }, cycle.digital_data)

class TestCreateAnalogWaveform(TestCycleBaseCase):
    def testWithNoInstructions(self):
        self.cycle.instructions = []
        self.cycle.create_analog_waveform()

        self.assertEqual([], self.cycle.analog_domain)

    def testIntervalSpacings(self):
        self.cycle.create_analog_waveform()

        expected_domain = [0.0, 1.0, 2.0, 3.0, 3.99, 4.98, 6.0, 7.01, 9.0]

        self.assertFloatListEqual(expected_domain, self.cycle.analog_domain)

class TestCreateNovatechWaveform(TestCycleBaseCase):
    def testWithNoInstructions(self):
        self.cycle.instructions = []
        self.cycle.create_novatech_waveform()

        self.assertEqual([], self.cycle.analog_domain)

    def testIntervalSpacings(self):
        self.cycle.create_novatech_waveform()

        expected_domain = [0.0, 1.0, 2.0, 3.0, 3.99, 4.98, 6.0, 7.01, 9.0]

        self.assertFloatListEqual(expected_domain, self.cycle.analog_domain)
