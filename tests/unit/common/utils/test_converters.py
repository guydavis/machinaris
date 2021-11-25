import os
import sys
import unittest

sys.path.insert(1, os.path.join(sys.path[0], '../../../..'))
from common.utils import converters

class TestRoundBalance(unittest.TestCase):

    def test_zero(self):
        data = 0
        result = converters.round_balance(data)
        self.assertEqual(result, "0")

    def test_neg_one(self):
        data = -1
        result = converters.round_balance(data)
        self.assertEqual(result, "-1.0")

    def test_plus_one(self):
        data = 1
        result = converters.round_balance(data)
        self.assertEqual(result, "1.0")

    def test_tenths(self):
        data = 0.2
        result = converters.round_balance(data)
        self.assertEqual(result, "0.2")

    def test_hundredths(self):
        data = 0.02
        result = converters.round_balance(data)
        self.assertEqual(result, "0.02")

    def test_thousandths(self):
        data = 0.002
        result = converters.round_balance(data)
        self.assertEqual(result, "0.002")
    
    def test_tenthousandths(self):
        data = 0.0002
        result = converters.round_balance(data)
        self.assertEqual(result, "0.0002")

    def test_hundredthousandths(self):
        data = 0.00002
        result = converters.round_balance(data)
        self.assertEqual(result, "0.0")
    
    def test_millionths(self):
        data = 0.000002
        result = converters.round_balance(data)
        self.assertEqual(result, "0.0")

    def test_singledigit(self):
        data = 2
        result = converters.round_balance(data)
        self.assertEqual(result, "2.0")

    def test_thousand(self):
        data = 2000
        result = converters.round_balance(data)
        self.assertEqual(result, "2,000")

    def test_tenthousand(self):
        data = 20000
        result = converters.round_balance(data)
        self.assertEqual(result, "20,000")

    def test_million(self):
        data = 2000000
        result = converters.round_balance(data)
        self.assertEqual(result, "2,000,000")
