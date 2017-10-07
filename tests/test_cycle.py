import unittest
import CycleControl.cycle as cycle
import CycleControl.instruction as instruction
import CycleControl.hardware_types as hardware_types

class TestCycleCreation(unittest.TestCase):
    def testCreationWithNoData(self):
        hardware = hardware_types.HardwareSetup()
        inst = instruction.Instruction(hardware = hardware)
        test_vars = {'test_var': 3}

        cycle_obj = cycle.Cycle([inst], {'test_var': 3})

        self.assertDictEqual(test_vars, cycle_obj.variables)

        self.assertEqual([], cycle_obj.analog_domain)
        self.assertEqual([], cycle_obj.novatech_domain)
        self.assertEqual([], cycle_obj.digital_domain)

        self.assertEqual({}, cycle_obj.analog_data)
        self.assertEqual({}, cycle_obj.novatech_data)
        self.assertEqual({}, cycle_obj.digital_data)

