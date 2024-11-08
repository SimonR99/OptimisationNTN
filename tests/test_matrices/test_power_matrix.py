import unittest

import numpy as np

from optimisation_ntn.algorithms.optimization_strategy import (
    AllOnStrategy,
    RandomStrategy,
)
from optimisation_ntn.matrices.decision_matrices import DecisionMatrices, MatrixType
from optimisation_ntn.networks.network import Network
from optimisation_ntn.networks.request import Request
from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.utils.position import Position


class TestPowerMatrix(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.network = Network()
        self.matrices = DecisionMatrices(dimension=3)

        # Create test nodes
        self.user1 = UserDevice(node_id=0, initial_position=Position(0, 0), request=Request(np.random.randint(1,100)))
        self.user2 = UserDevice(node_id=1, initial_position=Position(1000, 0), request=Request(np.random.randint(1,100)))
        self.bs1 = BaseStation(node_id=2, initial_position=Position(100, 0))

        # Add nodes to network
        for node in [self.user1, self.user2, self.bs1]:
            self.network.add_node(node)

    def test_all_on_strategy(self):
        """Test that AllOnStrategy sets all power states to 1"""
        strategy = AllOnStrategy(self.matrices, self.network)

        # Create some dummy history
        matrix_history = [
            {
                MatrixType.COVERAGE_ZONE: np.zeros((3, 3)),
                MatrixType.POWER_STATE: np.zeros((3, 3)),
                MatrixType.REQUEST: np.zeros((3, 3)),
                MatrixType.ASSIGNMENT: np.zeros((3, 3)),
            }
        ]

        # Run optimization
        power_matrix = strategy.optimize(matrix_history)

        # Check that all values are 1
        self.assertTrue(np.all(power_matrix.data == 1))

        # Check that matrix was properly set in DecisionMatrices
        stored_matrix = self.matrices.get_matrix(MatrixType.POWER_STATE)
        self.assertTrue(np.all(stored_matrix.data == 1))
