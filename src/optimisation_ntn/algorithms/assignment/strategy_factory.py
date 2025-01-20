""" Assignment strategy factory. Returns a strategy instance based on the name """

from typing import Dict, Type, Optional

from optimisation_ntn.networks.network import Network

from .assignment_strategy import AssignmentStrategy
from .closest_node import ClosestNodeAssignment
from .energy_greedy import EnergyGreedyAssignment
from .haps_only import HAPSOnlyAssignment
from .matrix_based import MatrixBasedAssignment
from .random_assignment import RandomAssignment
from .time_greedy import TimeGreedyAssignment
from .qlearning import QLearningAssignment


class AssignmentStrategyFactory:
    """Factory for creating assignment strategies"""

    _strategies: Dict[str, Type[AssignmentStrategy]] = {
        "TimeGreedy": TimeGreedyAssignment,
        "ClosestNode": ClosestNodeAssignment,
        "EnergyGreedy": EnergyGreedyAssignment,
        "HAPSOnly": HAPSOnlyAssignment,
        "Random": RandomAssignment,
        "MatrixBased": MatrixBasedAssignment,
        "QLearning": QLearningAssignment,
    }

    # Add optimization algorithms as valid strategies
    _optimization_strategies = {"GA", "PSO", "DE"}

    @classmethod
    def get_strategy(
        cls, strategy, network: Network, qtable_path: Optional[str] = None
    ) -> AssignmentStrategy:
        """Get assignment strategy instance from string name or class"""
        # Handle None case by returning default strategy
        if strategy is None:
            return cls._strategies["TimeGreedy"](network)

        if isinstance(strategy, str):
            # Check if it's an optimization strategy
            if strategy in cls._optimization_strategies:
                return cls._strategies["MatrixBased"](
                    network
                )  # Use MatrixBased for optimization

            if strategy not in cls._strategies:
                raise ValueError(f"Unknown strategy: {strategy}")

            # Only pass qtable_path to QLearning strategy
            if strategy == "QLearning":
                return cls._strategies[strategy](network, qtable_path=qtable_path)
            return cls._strategies[strategy](network)

        if isinstance(strategy, type) and issubclass(strategy, AssignmentStrategy):
            # Only pass qtable_path if it's QLearningAssignment
            if strategy == QLearningAssignment:
                return strategy(network, qtable_path=qtable_path)
            return strategy(network)

        if isinstance(strategy, AssignmentStrategy):
            return strategy

        raise ValueError(
            "Strategy must be a string name, AssignmentStrategy class, or instance"
        )

    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[AssignmentStrategy]):
        """Register a new assignment strategy"""
        if not issubclass(strategy_class, AssignmentStrategy):
            raise ValueError("Strategy must inherit from AssignmentStrategy")
        cls._strategies[name] = strategy_class

    @classmethod
    def available_strategies(cls) -> list[str]:
        """Get list of available strategy names"""
        return list(cls._strategies.keys()) + list(cls._optimization_strategies)
