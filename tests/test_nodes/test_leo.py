import unittest

from optimisation_ntn.nodes.leo import LEO
from optimisation_ntn.utils.type import Position


class TestLEO(unittest.TestCase):
    def test_speed(self):
        leo = LEO(1, Position(0, 0))
        self.assertAlmostEqual(leo.speed, 7616.5, places=0)

    def test_initial_angle(self):
        leo = LEO(1, Position(0, 0))
        self.assertAlmostEqual(leo.intial_angle, -13.6, places=0)
