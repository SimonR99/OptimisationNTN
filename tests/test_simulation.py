import pytest
from optimisation_ntn.simulation import Simulation, SimulationConfig


def test_main_runs():
    """Test that the main function runs without raising exceptions"""
    try:
        config = SimulationConfig(seed=42)
        simulation = Simulation(config=config)
        total_energy = simulation.run()
        assert total_energy is not None
    except Exception as e:
        pytest.fail(f"Main function raised an exception: {e}")
