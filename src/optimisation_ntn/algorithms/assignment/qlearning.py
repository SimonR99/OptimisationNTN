"""Q-Learning based assignment strategy"""

import numpy as np
from typing import List, Dict, Tuple, Optional
import pickle
import os
from ...networks.request import Request, RequestStatus
from ...nodes.base_node import BaseNode
from .assignment_strategy import AssignmentStrategy


class QLearningAssignment(AssignmentStrategy):
    """Assigns requests using Q-Learning"""

    def __init__(self, network, epsilon=0.1, alpha=0.1, gamma=0.9, qtable_path=None):
        self.network = network
        self.epsilon = epsilon  # Exploration rate
        self.alpha = alpha  # Learning rate
        self.gamma = gamma  # Discount factor
        self.q_table: Dict[str, np.ndarray] = {}
        self.last_state = None
        self.last_action = None
        self.debug = False
        self.last_request = None

        # Load Q-table if path provided
        if qtable_path and os.path.exists(qtable_path):
            with open(qtable_path, "rb") as f:
                self.q_table = pickle.load(f)

    def get_state(self, request: Request, nodes: List[BaseNode]) -> str:
        """Convert current system state to a string representation"""
        state_parts = []

        # Add node states
        for node in nodes:
            # Node on/off state
            state_parts.append(str(int(node.state)))

            # Battery level (discretized to 10 levels)
            if node.battery_capacity == -1:
                battery_level = 5
            else:
                remaining = (
                    node.battery_capacity - node.energy_consumed
                ) / node.battery_capacity
                battery_level = max(0, int(remaining * 5))
            state_parts.append(str(battery_level))

            # Queue length (capped at 5)
            state_parts.append(str(min(5, len(node.processing_queue))))

            # Can process request
            state_parts.append(str(int(node.can_process(request))))

        # Request size category (small: 0, medium: 1, large: 2)
        size_category = 0
        if request.size > 5e6:
            size_category = 2
        elif request.size > 3e6:
            size_category = 1
        state_parts.append(str(size_category))

        return "_".join(state_parts)

    def get_q_values(self, state: str, num_actions: int) -> np.ndarray:
        """Get Q-values for a state, initializing if needed"""
        if state not in self.q_table:
            self.q_table[state] = np.zeros(num_actions)
        return self.q_table[state]

    def select_compute_node(
        self, request: Request, nodes: List[BaseNode]
    ) -> tuple[BaseNode, List[BaseNode], float]:
        if self.last_request is not None:
            if self.last_request.status == RequestStatus.COMPLETED:
                selected_node = nodes[self.last_action]

                # Calculate processing energy
                processing_time = (
                    self.last_request.size
                    * selected_node.cycle_per_bit
                    / selected_node.processing_frequency
                )
                processing_energy = selected_node.processing_energy() * processing_time

                # Calculate transmission energy - use the first link's bandwidth as reference
                # Find the communication link for this node
                for link in self.network.communication_links:
                    if link.node_b == selected_node:
                        transmission_time = (
                            self.last_request.size / link.config.total_bandwidth
                        )
                        transmission_energy = (
                            selected_node.transmission_energy() * transmission_time
                        )
                        break
                else:
                    # If no link found, only use processing energy
                    transmission_energy = 0

                # Total energy consumed
                total_energy = processing_energy + transmission_energy
                reward = -total_energy / 1000
            else:
                reward = -1.0

            self.update(reward, request, nodes)

        state = self.get_state(request, nodes)
        q_values = self.get_q_values(state, len(nodes))

        # Epsilon-greedy action selection
        if np.random.random() < self.epsilon:
            action = np.random.randint(len(nodes))
        else:
            action = np.argmax(q_values)

        self.last_state = state
        self.last_action = action
        self.last_request = request

        selected_node = nodes[action]
        path = self.network.generate_request_path(request.current_node, selected_node)
        total_delay = self.network.get_network_delay(request, path)

        if self.debug:
            print(f"Q values: {q_values}, for state {state}")
            print(f"Selected node {action} with Q-values: {q_values}")

        return selected_node, path, total_delay

    def update(
        self, reward: float, new_request: Optional[Request], nodes: List[BaseNode]
    ):
        """Update Q-values based on reward and new state"""
        if self.last_state is None:
            return

        if new_request is None:
            # Terminal state - only use immediate reward
            old_value = self.q_table[self.last_state][self.last_action]
            new_value = (1 - self.alpha) * old_value + self.alpha * reward
        else:
            # Non-terminal state - use Q-learning update
            new_state = self.get_state(new_request, nodes)
            new_q_values = self.get_q_values(new_state, len(nodes))

            old_value = self.q_table[self.last_state][self.last_action]
            next_max = np.max(new_q_values)
            new_value = (1 - self.alpha) * old_value + self.alpha * (
                reward + self.gamma * next_max
            )

        self.q_table[self.last_state][self.last_action] = new_value

        if self.debug:
            print(f"Updated Q-value from {old_value:.2f} to {new_value:.2f}")

    def save_qtable(self, path: str):
        """Save Q-table to file"""
        with open(path, "wb") as f:
            pickle.dump(self.q_table, f)
