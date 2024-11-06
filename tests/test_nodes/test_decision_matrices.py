import unittest

import numpy as np

from optimisation_ntn.matrices.decision_matrices import DecisionMatrices, MatrixType
from optimisation_ntn.networks.network import Network
from optimisation_ntn.nodes.base_station import BaseStation
from optimisation_ntn.nodes.user_device import UserDevice
from optimisation_ntn.utils.position import Position


class TestDecisionMatrices(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.network = Network()
        self.decision_matrices = DecisionMatrices(dimension=3)

        # Create test nodes with known positions
        self.user1 = UserDevice(node_id=0, initial_position=Position(0, 0))
        self.user2 = UserDevice(node_id=1, initial_position=Position(1000, 0))
        self.user3 = UserDevice(node_id=2, initial_position=Position(6000, 0))

        self.bs1 = BaseStation(node_id=3, initial_position=Position(100, 0))
        self.bs2 = BaseStation(node_id=4, initial_position=Position(2000, 0))
        self.bs3 = BaseStation(node_id=5, initial_position=Position(3000, 0))

        # Add nodes to network
        for node in [self.user1, self.user2, self.user3, self.bs1, self.bs2, self.bs3]:
            self.network.add_node(node)

    def test_large_coverage_radius(self):
        """Test coverage zones with 5000m radius - all users should connect"""
        self.decision_matrices.compute_coverage_zones(
            self.network, coverage_radius=5000
        )
        coverage_matrix = self.decision_matrices.get_matrix(
            MatrixType.COVERAGE_ZONE
        ).data

        expected_matrix = np.array(
            [
                [1, 0, 0],  # user1 -> bs1
                [1, 0, 0],  # user2 -> bs1
                [0, 0, 1],  # user3 -> bs2
            ]
        )

        np.testing.assert_array_equal(
            coverage_matrix,
            expected_matrix,
            err_msg=f"Coverage matrix with 5000m radius incorrect.\nExpected:\n{expected_matrix}\nGot:\n{coverage_matrix}",
        )

    def test_small_coverage_radius(self):
        """Test coverage zones with 1500m radius - only nearby users should connect"""
        self.decision_matrices.compute_coverage_zones(
            self.network, coverage_radius=1500
        )
        coverage_matrix = self.decision_matrices.get_matrix(
            MatrixType.COVERAGE_ZONE
        ).data

        expected_matrix = np.array(
            [
                [1, 0, 0],  # user1 -> bs1
                [1, 0, 0],  # user2 -> bs1
                [0, 0, 0],  # user3 -> no connection (out of range)
            ]
        )

        np.testing.assert_array_equal(
            coverage_matrix,
            expected_matrix,
            err_msg=f"Coverage matrix with 1500m radius incorrect.\nExpected:\n{expected_matrix}\nGot:\n{coverage_matrix}",
        )

    def test_zero_coverage_radius(self):
        """Test coverage zones with 0m radius - no connections should be made"""
        self.decision_matrices.compute_coverage_zones(self.network, coverage_radius=0)
        coverage_matrix = self.decision_matrices.get_matrix(
            MatrixType.COVERAGE_ZONE
        ).data

        expected_matrix = np.zeros((3, 3))

        np.testing.assert_array_equal(
            coverage_matrix,
            expected_matrix,
            err_msg=f"Coverage matrix with 0m radius should be all zeros.\nGot:\n{coverage_matrix}",
        )
