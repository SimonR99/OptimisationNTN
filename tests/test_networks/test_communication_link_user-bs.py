import logging
import unittest

import numpy as np

from optimisation_ntn.networks.communication_link import CommunicationLink, LinkConfig
from optimisation_ntn.networks.request import Request
from optimisation_ntn.nodes.base_node import BaseNode
from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.leo import LEO
from optimisation_ntn.utils.position import Position


def get_tick():
    """Get a random tick"""
    return np.random.randint(0, 100)


class TestCommunicationLink(unittest.TestCase):
    def setUp(self):
        # Define positions for nodes
        self.position_a = Position(0, 0)
        self.position_b = Position(300, 400)

        # Define nodes with antennas
        self.node_a = UserDevice(0, self.position_a)
        self.node_a.add_antenna("VHF", 3)  # Add compatible UHF antenna

        self.node_b = BaseStation(1, self.position_b)
        self.node_b.add_antenna("VHF", 10)  # Matching UHF antenna for communication

    def test_distance(self):
        # Test distance calculation
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            LinkConfig(total_bandwidth=174e3, signal_power=23, carrier_frequency=2e9),
        )
        self.assertEqual(link.link_length, 500.0)

    def test_linear_scale_db(self):
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            LinkConfig(total_bandwidth=174e3, signal_power=23, carrier_frequency=2e9),
        )
        self.assertEqual(link.linear_scale_db(40), 10000.0)

    def test_linear_scale_power_dbm(self):
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            LinkConfig(total_bandwidth=174e3, signal_power=23, carrier_frequency=2e9),
        )
        self.assertEqual(
            link.linear_scale_dbm(link.config.signal_power), 10 ** ((23 - 30) / 10)
        )

    def test_linear_scale_noise_dbm(self):
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            LinkConfig(total_bandwidth=174e3, signal_power=23, carrier_frequency=2e9),
        )
        self.assertEqual(
            link.linear_scale_dbm(self.node_a.spectral_noise_density),
            10 ** ((-174 - 30) / 10),
        )

    def test_gain(self):
        # Test Path Loss user-base station
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            LinkConfig(total_bandwidth=174e3, signal_power=23, carrier_frequency=2e9),
        )
        self.assertEqual(link.calculate_gain(), 9 / 12500)

    def test_bandwidth(self):
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            LinkConfig(total_bandwidth=174e3, signal_power=23, carrier_frequency=2e9),
        )
        self.assertEqual(link.adjusted_bandwidth, 174e3)

    def test_noise_power(self):
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            LinkConfig(total_bandwidth=174e3, signal_power=23, carrier_frequency=2e9),
        )
        self.assertEqual(link.noise_power, (10 ** ((-174 - 30) / 10)) * 174e3)

    def test_snr(self):
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            LinkConfig(total_bandwidth=174e3, signal_power=23, carrier_frequency=2e9),
        )
        self.assertAlmostEqual(link.calculate_snr(), 207387820811.28, places=0)

    def test_capacity(self):
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            LinkConfig(total_bandwidth=174e3, signal_power=23, carrier_frequency=2e9),
        )
        self.assertAlmostEqual(link.calculate_capacity(), 6541275.9975462, places=0)

    def test_calcul_leo_loss(self):
        # Set up a HAPS and LEO node. They both should have the right antennas
        node_haps = HAPS(0, Position(0, 0))
        node_leo = LEO(1)

        # Communication link between HAPS and LEO
        link = CommunicationLink(node_haps, node_leo, LinkConfig(1, 1, 1))
        self.assertNotEqual(
            link.calculate_free_space_path_loss(), 0.0
        )  # FSPL should not be zero

    def test_single_request(self):
        # Set up a communication link with compatible antennas and a request
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            LinkConfig(total_bandwidth=100e6, signal_power=23, carrier_frequency=2e9),
        )

        # Create and add a request
        request = Request(0, 0.1, self.node_a, get_tick, self.node_b)
        request.set_size(100)  # data_size=100 bits
        link.add_to_queue(request)

        # Process request in the queue with sufficient time
        for _ in range(10):
            link.tick(0.1)
            print(link.request_progress)

        self.assertEqual(len(link.transmission_queue), 0)

    def test_multiple_requests(self):
        # Set up a communication link with compatible antennas and multiple requests
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            LinkConfig(total_bandwidth=100e6, signal_power=23, carrier_frequency=2e9),
        )

        # Create and add multiple requests
        request1 = Request(0, 0.1, self.node_a, get_tick, self.node_b)
        request1.set_size(20e6)  # data size=20 Mbits
        request2 = Request(0, 0.1, self.node_a, get_tick, self.node_b)
        request2.set_size(10e6)  # data size=10 Mbits

        link.add_to_queue(request1)
        link.add_to_queue(request2)

        self.assertEqual(len(link.transmission_queue), 2)

        link.tick(0.1)

        self.assertEqual(len(link.transmission_queue), 1)

        link.tick(0.1)

        self.assertEqual(len(link.transmission_queue), 0)
