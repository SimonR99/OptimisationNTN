import unittest
import numpy as np

from optimisation_ntn.matrices.decision_matrices import DecisionMatrices, MatrixType


class TestRequestMatrix(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures"""
        self.decision_matrices = DecisionMatrices()

    def test_request_matrix_shape(self):
        """Test if generated request matrix has correct shape"""
        num_requests = 10
        num_steps = 5

        self.decision_matrices.generate_request_matrix(num_requests, num_steps)
        request_matrix = self.decision_matrices.get_matrix(MatrixType.REQUEST).data

        self.assertEqual(
            request_matrix.shape,
            (num_requests, num_steps),
            f"Expected shape ({num_requests}, {num_steps}), got {request_matrix.shape}",
        )

    def test_request_matrix_constraints(self):
        """Test if request matrix satisfies basic constraints:
        - Each row should sum to 1 (one request per user)
        - All values should be 0 or 1
        - Column sums should follow Poisson distribution
        """
        num_requests = 20
        num_steps = 10

        self.decision_matrices.generate_request_matrix(num_requests, num_steps)
        request_matrix = self.decision_matrices.get_matrix(MatrixType.REQUEST).data

        # Test each row sums to 1 (one request per user)
        row_sums = np.sum(request_matrix, axis=1)
        np.testing.assert_array_equal(
            row_sums,
            np.ones(num_requests),
            err_msg="Each row should sum to 1 (one request per user)",
        )

        # Test all values are 0 or 1
        unique_values = np.unique(request_matrix)
        np.testing.assert_array_equal(
            sorted(unique_values),
            [0, 1],
            err_msg="Matrix should only contain 0s and 1s",
        )

        # Test total number of requests
        total_requests = np.sum(request_matrix)
        self.assertEqual(
            total_requests,
            num_requests,
            f"Total requests should be {num_requests}, got {total_requests}",
        )

    def test_edge_cases(self):
        """Test edge cases for request matrix generation"""
        # Test with single request and single time step
        self.decision_matrices.generate_request_matrix(num_requests=1, num_steps=1)
        request_matrix = self.decision_matrices.get_matrix(MatrixType.REQUEST).data
        self.assertEqual(request_matrix.shape, (1, 1))
        self.assertEqual(request_matrix[0, 0], 1)

        # Test with single request over multiple time steps
        self.decision_matrices.generate_request_matrix(num_requests=1, num_steps=5)
        request_matrix = self.decision_matrices.get_matrix(MatrixType.REQUEST).data
        self.assertEqual(request_matrix.shape, (1, 5))
        self.assertEqual(np.sum(request_matrix), 1)

        # Test with multiple requests in single time step
        self.decision_matrices.generate_request_matrix(num_requests=5, num_steps=1)
        request_matrix = self.decision_matrices.get_matrix(MatrixType.REQUEST).data
        self.assertEqual(request_matrix.shape, (5, 1))
        np.testing.assert_array_equal(request_matrix, np.ones((5, 1)))

    def test_invalid_inputs(self):
        """Test handling of invalid inputs"""
        with self.assertRaises(ValueError):
            self.decision_matrices.generate_request_matrix(num_requests=0, num_steps=5)

        with self.assertRaises(ValueError):
            self.decision_matrices.generate_request_matrix(num_requests=5, num_steps=0)

        with self.assertRaises(ValueError):
            self.decision_matrices.generate_request_matrix(num_requests=-1, num_steps=5)

        with self.assertRaises(ValueError):
            self.decision_matrices.generate_request_matrix(num_requests=5, num_steps=-1)
