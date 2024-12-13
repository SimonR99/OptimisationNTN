""" Assignment strategy factory. Returns a strategy instance based on the name """

from typing import Type, Dict
from .assignment_strategy import AssignmentStrategy
from .time_greedy import TimeGreedyAssignment
from .closest_node import ClosestNodeAssignment
from .energy_greedy import EnergyGreedyAssignment
from .haps_only import HAPSOnlyAssignment
from .random_assignment import RandomAssignment
from .matrix_based import MatrixBasedAssignment
from optimisation_ntn.networks.network import Network


class AssignmentStrategyFactory:
    """Factory class for creating assignment strategies"""

    _strategies: Dict[str, Type[AssignmentStrategy]] = {
        "TimeGreedy": TimeGreedyAssignment,
        "ClosestNode": ClosestNodeAssignment,
        "EnergyGreedy": EnergyGreedyAssignment,
        "HAPSOnly": HAPSOnlyAssignment,
        "Random": RandomAssignment,
        "MatrixBased": MatrixBasedAssignment,
    }

    @classmethod
    def get_strategy(cls, strategy, network: Network) -> AssignmentStrategy:
        """Get assignment strategy instance from string name or class"""
        if isinstance(strategy, str):
            if strategy not in cls._strategies:
                raise ValueError(f"Unknown strategy: {strategy}")
            return cls._strategies[strategy](network)
        elif isinstance(strategy, type) and issubclass(strategy, AssignmentStrategy):
            return strategy(network)
        elif isinstance(strategy, AssignmentStrategy):
            return strategy
        else:
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
        return list(cls._strategies.keys())
