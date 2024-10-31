import unittest

import numpy as np

from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.leo import LEO
from optimisation_ntn.utils.communication_link import CommunicationLink
from optimisation_ntn.utils.type import Position


class TestLEO(unittest.TestCase):
    def test_speed(self):
        leo = LEO(1)
        self.assertAlmostEqual(leo.speed, 7616.5, places=0)

    def test_angular_speed(self):
        leo = LEO(1)
        self.assertAlmostEqual(leo.angular_speed, 0.064, places=2)

    def test_initial_angle(self):
        leo = LEO(1)
        self.assertAlmostEqual(leo.initial_angle, -13.6, places=0)

    def test_mid_point_position_distance(self):
        leo = LEO(1, 0)
        haps = HAPS(2, initial_position=Position(0.0, 20e3))

        link = CommunicationLink(leo, haps, 1, 1, 1)

        self.assertEqual(link.link_length, leo.position.y - haps.position.y)
        self.assertEqual(link.link_length, 480e3)

    def test_max_position_distance(self):
        start_leo = LEO(1, LEO.initial_angle)
        end_leo = LEO(2, LEO.final_angle)
        haps = HAPS(2, initial_position=Position(0.0, 20e3))

        first_link = CommunicationLink(start_leo, haps, 1, 1, 1)
        second_link = CommunicationLink(end_leo, haps, 1, 1, 1)

        self.assertAlmostEqual(first_link.link_length, 1646550.0, places=0)
        self.assertAlmostEqual(second_link.link_length, 1646550.0, places=0)

    def test_tick_speed(self):
        # The total orbit time of the satellite is 94.47 minutes (5668.22432) as calculated in the system model
        total_orbit_time_in_seconds = 5668.22432
        time_to_middle_point = (
            total_orbit_time_in_seconds * np.abs(LEO.initial_angle) / 360
        )

        leo_midpoint = LEO(1, LEO.initial_angle)
        leo_midpoint.tick(time_to_middle_point)

        leo_orbit = LEO(2, 0.0)
        leo_orbit.tick(total_orbit_time_in_seconds)

        self.assertAlmostEqual(leo_midpoint.position.x, 0.0, places=0)
        self.assertAlmostEqual(leo_midpoint.position.y, 500e3, places=0)

        self.assertAlmostEqual(leo_orbit.position.x, 0.0, places=0)
        self.assertAlmostEqual(leo_orbit.position.y, 500e3, places=0)
