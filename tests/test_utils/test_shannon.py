import unittest

from optimisation_ntn.utils.shannon import shannon_capacity


class TestShannon(unittest.TestCase):

    def test_shannon_capacity_positive_values(self):
        bandwidth = 1e6
        signal_power = 1e-3
        noise_power = 1e-6
        expected_capacity = 9967226.25884
        result = shannon_capacity(bandwidth, signal_power, noise_power)
        self.assertAlmostEqual(result, expected_capacity, places=5)
