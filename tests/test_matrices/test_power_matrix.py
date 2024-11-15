import unittest

import numpy as np

from optimisation_ntn.algorithms.power_strategy import (
    AllOnStrategy,
    RandomStrategy,
)


class TestPowerMatrix(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.num_devices = 5
        self.num_steps = 10

    def test_all_on_strategy(self):
        """Test that AllOnStrategy sets all power states to 1"""
        strategy = AllOnStrategy()
        power_matrix = strategy.generate_power_matrix(self.num_devices, self.num_steps)

        # Check matrix shape
        self.assertEqual(power_matrix.shape, (self.num_devices, self.num_steps))
        
        # Check that all values are 1
        self.assertTrue(np.all(power_matrix == 1))

    def test_random_strategy(self):
        """Test that RandomStrategy generates valid random matrices"""
        probability = 0.7
        strategy = RandomStrategy(probability=probability)
        power_matrix = strategy.generate_power_matrix(self.num_devices, self.num_steps)

        # Check matrix shape
        self.assertEqual(power_matrix.shape, (self.num_devices, self.num_steps))
        
        # Check that all values are binary (0 or 1)
        self.assertTrue(np.all(np.logical_or(power_matrix == 0, power_matrix == 1)))
        
        # Check that the proportion of 1s is roughly equal to the probability
        # (allowing for some random variation)
        proportion_ones = np.mean(power_matrix)
        self.assertGreater(proportion_ones, probability - 0.2)
        self.assertLess(proportion_ones, probability + 0.2)

    def test_random_strategy_edge_cases(self):
        """Test RandomStrategy with edge case probabilities"""
        # Test p=1 (should be all ones)
        strategy = RandomStrategy(probability=1.0)
        power_matrix = strategy.generate_power_matrix(self.num_devices, self.num_steps)
        self.assertTrue(np.all(power_matrix == 1))

        # Test p=0 (should be all zeros)
        strategy = RandomStrategy(probability=0.0)
        power_matrix = strategy.generate_power_matrix(self.num_devices, self.num_steps)
        self.assertTrue(np.all(power_matrix == 0))
