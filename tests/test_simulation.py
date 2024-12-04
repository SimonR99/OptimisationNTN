import pytest

from optimisation_ntn.algorithms.power_strategy import AllOnStrategy
from optimisation_ntn.simulation import Simulation


def test_main_runs():
    """Test that the main function runs without raising exceptions"""
    try:
        simulation = Simulation(strategy=AllOnStrategy())

        total_energy = simulation.run(None)
        assert total_energy is not None
    except Exception as e:
        pytest.fail(f"Main function raised an exception: {e}")
