import logging
import unittest

import numpy as np

from optimisation_ntn.networks.request import Request
from optimisation_ntn.nodes.base_node import BaseNode
from optimisation_ntn.nodes.haps import HAPS
from optimisation_ntn.nodes.leo import LEO
from optimisation_ntn.utils.communication_link import CommunicationLink
from optimisation_ntn.utils.position import Position


class TestCommunicationLink(unittest.TestCase):
    def setUp(self):
        # Define positions for nodes
        self.position_a = Position(0, 0)
        self.position_b = Position(3, 4)

        # Define nodes with antennas
        self.node_a = BaseNode(0, self.position_a)
        self.node_a.add_antenna("UHF", 1.5)  # Add compatible UHF antenna

        self.node_b = BaseNode(1, self.position_b)
        self.node_b.add_antenna("UHF", 1.2)  # Matching UHF antenna for communication

    def test_zero_capacity(self):
        # Test with zero signal power
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            total_bandwidth=1,
            signal_power=0,
            carrier_frequency=1,
        )
        self.assertEqual(link.calculate_capacity(), 0.0)

    def test_distance(self):
        # Test distance calculation
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            total_bandwidth=1,
            signal_power=1,
            carrier_frequency=1,
        )
        self.assertEqual(link.link_length, 5.0)

    def test_calcul_leo_loss(self):
        # Set up a HAPS and LEO node. They both should have the right antennas
        node_haps = HAPS(0, Position(0, 0))
        node_leo = LEO(1)

        # Communication link between HAPS and LEO
        link = CommunicationLink(
            node_haps, node_leo, total_bandwidth=1, signal_power=1, carrier_frequency=1
        )
        self.assertNotEqual(link.calculate_fspl(), 0.0)  # FSPL should not be zero

    def test_single_request(self):
        # Set up a communication link with compatible antennas and a request
        link = CommunicationLink(
            self.node_a,
            self.node_b,
            total_bandwidth=1,
            signal_power=1,
            carrier_frequency=1,
        )

        # Create and add a request
        request = Request(np.random.randint(0,100))
        request.set_size(100) # data_size=100 bits
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
            total_bandwidth=1,
            signal_power=1,
            carrier_frequency=1,
        )

        # Create and add multiple requests
        request1 = Request(np.random.randint(0,100))
        request1.set_size(200) # data size=200 bits
        request2 = Request(np.random.randint(0,100))
        request2.set_size(100) # data size=100 bits

        link.add_to_queue(request1)
        link.add_to_queue(request2)

        self.assertEqual(len(link.transmission_queue), 2)

        for _ in range(20):  # Take longer time to process since requests is larger
            link.tick(0.1)

        self.assertEqual(len(link.transmission_queue), 1)

        for _ in range(10):
            print(len(link.transmission_queue))
            link.tick(0.1)

        self.assertEqual(len(link.transmission_queue), 0)
