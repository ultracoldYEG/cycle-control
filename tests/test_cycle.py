import unittest
from CycleControl import *

class TestCycle(unittest.TestCase):
    def testOne(self):
        print '1', '2', 1==2
        self.assertEqual(1, 2, '1 == 2')
