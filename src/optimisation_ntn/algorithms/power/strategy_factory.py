"""Power strategy factory"""

from typing import Dict, Type

from .all_on import AllOnPowerStrategy
from .on_demand import OnDemandPowerStrategy
from .on_demand_timeout import OnDemandWithTimeoutPowerStrategy
from .random_strategy import RandomPowerStrategy
from .power_strategy import PowerStrategy


class PowerStrategyFactory:
    """Factory class for creating power strategies"""

    _strategies: Dict[str, Type[PowerStrategy]] = {
        "AllOn": AllOnPowerStrategy,
        "OnDemand": OnDemandPowerStrategy,
        "OnDemandWithTimeout": OnDemandWithTimeoutPowerStrategy,
        "Random": RandomPowerStrategy,
    }

    @classmethod
    def get_strategy(cls, strategy: str, **kwargs) -> PowerStrategy:
        """Get power strategy instance from string name"""
        if strategy not in cls._strategies:
            raise ValueError(f"Unknown power strategy: {strategy}")
        return cls._strategies[strategy](**kwargs)

    @classmethod
    def register_strategy(cls, name: str, strategy_class: Type[PowerStrategy]):
        """Register a new power strategy"""
        if not issubclass(strategy_class, PowerStrategy):
            raise ValueError("Strategy must inherit from PowerStrategy")
        cls._strategies[name] = strategy_class

    @classmethod
    def available_strategies(cls) -> list[str]:
        """Get list of available strategy names"""
        return list(cls._strategies.keys())
