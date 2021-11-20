import os
import sys
import unittest

sys.path.insert(1, os.path.join(sys.path[0], '../../../..'))
from common.utils import converters

class TestRoundBalance(unittest.TestCase):

    def test_zero(self):
        data = 0
        result = converters.round_balance(data)
        self.assertEqual(result, "0.0")

    def test_neg_one(self):
        data = -1
        result = converters.round_balance(data)
        self.assertEqual(result, "-1.0")

    def test_plus_one(self):
        data = 1
        result = converters.round_balance(data)
        self.assertEqual(result, "1.0")

    def test_two_million(self):
        data = 2000000
        result = converters.round_balance(data)
        self.assertEqual(result, "2000000")
