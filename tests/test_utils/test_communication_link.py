import unittest

from optimisation_ntn.utils.communication_link import CommunicationLink


class TestCommunicationLink(unittest.TestCase):
    def test_zero_capacity(self):
        link = CommunicationLink(None, None, 1, 0, 1)
        self.assertEqual(link.capacity, 0.0)
