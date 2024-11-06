from abc import ABC, abstractmethod
import numpy as np
from ..matrices.decision_matrices import DecisionMatrices
from ..networks.network import Network

class BaseOptimizer(ABC):
    def __init__(self, matrices: DecisionMatrices, network: Network):
        self.matrices = matrices
        self.network = network

    @abstractmethod
    def optimize_power_states(self):
        """Optimize power states of network nodes"""
        pass

    @abstractmethod
    def initialize(self):
        """Initialize optimizer parameters"""
        pass

    def evaluate_power_efficiency(self) -> float:
        """Evaluate power efficiency of current state"""
        power_matrix = self.matrices.get_matrix('B').data
        coverage_matrix = self.matrices.get_matrix('A').data
        request_matrix = self.matrices.get_matrix('K').data
        
        # Calculate total power consumption
        power_consumption = np.sum(power_matrix)
        if power_consumption == 0:
            return 0.0
            
        # Calculate service coverage
        service_coverage = np.sum(coverage_matrix * power_matrix)
        
        # Calculate request satisfaction
        request_satisfaction = np.sum(request_matrix * power_matrix)
        
        # Return efficiency metric
        return (service_coverage + request_satisfaction) / power_consumption