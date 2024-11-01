import numpy as np
from typing import Dict

from ..nodes.base_station import BaseStation
from ..nodes.haps import HAPS
from ..nodes.leo import LEO
from ..nodes.user_device import UserDevice
from .matrix import Matrix

class DecisionMatrices:
    def __init__(self, dimension: int):
        self.matrices: Dict[str, Matrix] = {
            'A': Matrix(dimension, dimension, "Coverage Zone Matrix"),  # Pre-computed coverage zones
            'B': Matrix(dimension, dimension, "Power State Matrix"),    # Power state decisions (to optimize)
            'K': Matrix(dimension, dimension, "Request Matrix"),        # Request generation (Poisson)
            'X': Matrix(dimension, dimension, "Assignment Matrix")      # Real-time request assignment
        }
        
    def compute_coverage_zones(self, network):
        """Pre-compute coverage zones for base stations"""
        users = [n for n in network.nodes if isinstance(n, UserDevice)]
        base_stations = [n for n in network.nodes if isinstance(n, BaseStation)]
        
        coverage_matrix = np.zeros((len(users), len(base_stations)))
        
        for i, user in enumerate(users):
            for j, bs in enumerate(base_stations):
                distance = user.position.distance_to(bs.position)
                # Set 1 if user is within coverage radius
                coverage_matrix[i, j] = 1 if distance <= bs.coverage_radius else 0
                
        self.matrices['A'].update(coverage_matrix)
    
    def generate_request_matrix(self, num_users: int, simulation_time: float, mean_arrival_rate: float = 0.1):
        """Generate request matrix using Poisson distribution"""
        request_matrix = np.zeros((num_users, int(simulation_time)))
        
        for user in range(num_users):
            # Generate Poisson process for request arrivals
            arrivals = np.random.poisson(mean_arrival_rate, int(simulation_time))
            request_matrix[user, :] = arrivals
            
        self.matrices['K'].update(request_matrix)
    
    def update_assignment_matrix(self, network):
        """Update real-time request assignment matrix"""
        users = [n for n in network.nodes if isinstance(n, UserDevice)]
        servers = [n for n in network.nodes if isinstance(n, (BaseStation, HAPS, LEO))]
        
        assignment_matrix = np.zeros((len(users), len(servers)))
        
        # Assign requests based on current network state and active links
        for i, user in enumerate(users):
            for j, server in enumerate(servers):
                for link in network.communication_links:
                    if link.node_a == user and link.node_b == server:
                        assignment_matrix[i, j] = 1 if link.transmission_queue else 0
                        
        self.matrices['X'].update(assignment_matrix)
    
    def get_matrix(self, name: str) -> Matrix:
        return self.matrices[name]
    
    def set_matrix(self, name: str, matrix: Matrix):
        if name in self.matrices:
            self.matrices[name] = matrix
        else:
            raise ValueError(f"Unknown matrix name: {name}")