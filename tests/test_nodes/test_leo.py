import unittest

from optimisation_ntn.nodes.leo import LEO


class TestLEO(unittest.TestCase):
    def test_speed(self):
        leo = LEO(1)
        self.assertAlmostEqual(leo.speed, 7616.5, places=0)
