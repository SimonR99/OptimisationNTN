import unittest

from optimisation_ntn.nodes.base_node import BaseNode
from optimisation_ntn.utils.communication_link import CommunicationLink
from optimisation_ntn.utils.type import Position


class TestCommunicationLink(unittest.TestCase):
    def test_zero_capacity(self):
        link = CommunicationLink(None, None, 1, 0, 1)
        self.assertEqual(link.capacity, 0.0)

    def test_distance(self):
        node_a = BaseNode(0, Position(0, 0))
        node_b = BaseNode(1, Position(3, 4))

        link = CommunicationLink(node_a, node_b, 1, 1, 1)

        self.assertEqual(link.link_length, 5.0)
