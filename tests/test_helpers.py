import unittest
import CycleControl.helpers as helpers

from PyQt5.QtCore import Qt

class TestBoolToCheckstate(unittest.TestCase):
    def testWhenFalse(self):
        self.assertEqual(Qt.Unchecked, helpers.bool_to_checkstate(False))

    def testWhenTrue(self):
        self.assertEqual(Qt.Checked, helpers.bool_to_checkstate(True))

class TestReplaceBit(unittest.TestCase):
    def testResult(self):
        self.assertEqual('001000100', helpers.replace_bit('001010100', 4, '0'))

class TestParseFunction(unittest.TestCase):
    def testWithConstant(self):
        func, args = helpers.parse_function('3.14159', {})
        self.assertEqual('const', func)
        self.assertEqual([3.14159], args)

    def testWithFunction(self):
        func, args = helpers.parse_function('test_function(2.1,5.4,7.4)', {})
        self.assertEqual('test_function', func)
        self.assertEqual([2.1, 5.4, 7.4], args)

    def testWithVariables(self):
        func, args = helpers.parse_function('test_function(arg1,arg2,arg3)', {'arg1': 40, 'arg2': 76, 'arg3':8.7})
        self.assertEqual('test_function', func)
        self.assertEqual([40, 76, 8.7], args)

    def testWithInvalidVariable(self):
        func, args = helpers.parse_function('test_function(arg1,arg2,missing)', {'arg1': 40, 'arg2': 76, 'arg3':8.7})
        self.assertEqual(None, func)
        self.assertEqual(None, args)

    def testWithInvalidForm(self):
        func, args = helpers.parse_function('bad_function', {})
        self.assertEqual(None, func)
        self.assertEqual(None, args)

class TestParseArg(unittest.TestCase):
    def testWithConstant(self):
        self.assertEqual(3.14159, helpers.parse_arg('3.14159', {}))

    def testWithVariables(self):
        self.assertEqual(76, helpers.parse_arg('arg2', {'arg1': 40, 'arg2': 76, 'arg3':8.7}))

    def testWithInvalidVariable(self):
        self.assertEqual(None, helpers.parse_arg('missing', {'arg1': 40, 'arg2': 76, 'arg3':8.7}))

class TestForceEven(unittest.TestCase):
    def testWithEvenArray(self):
        self.assertEqual([1, 2, 3, 4, 5, 6], helpers.force_even([1, 2, 3, 4, 5, 6]))

    def testWithOddArray(self):
        self.assertEqual([1, 2, 3, 4], helpers.force_even([1, 2, 3, 4, 5]))
