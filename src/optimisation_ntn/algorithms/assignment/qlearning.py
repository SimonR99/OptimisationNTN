"""Q-Learning based assignment strategy"""

import numpy as np
from typing import List, Dict
import pickle
import os

from optimisation_ntn.networks.network import Network
from ...networks.request import Request, RequestStatus
from ...nodes.base_node import BaseNode
from .assignment_strategy import AssignmentStrategy


class QLearningAssignment(AssignmentStrategy):
    """Assigns requests using Q-Learning"""

    def __init__(
        self,
        network,
        epsilon=0.0,
        alpha=0.1,
        gamma=0.9,
        qtable_path=None,
    ):
        self.network: Network = network
        # Set very low epsilon if using a pre-trained model
        self.epsilon = epsilon
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
                # print the first 10 states and their corresponding q-values
                # print(f"Number of states: {len(self.q_table)}")

        # Add new attributes for tracking request history
        self.pending_requests = {}  # Dict[request_id, (state, action, start_time)]
        self.all_requests = {}  # Dict[request_id, (state, action, start_time)]

    def get_state(self, request: Request, nodes: List[BaseNode]) -> str:
        """Convert current system state to a string representation

        State format for each node:
        - on/off state (1/0)
        - remaining battery category (i/-1/l/m/h for infinite/-1/<100/<1000/>=1000)
        - can process (1/0)
        - processing power category (J/Mbit)
        """
        state_parts = []

        # Request features - keep the existing size categorization
        size_category = 0
        if request.size > 5e6:
            size_category = 2
        elif request.size > 3e6:
            size_category = 1
        state_parts.append(f"s{size_category}")  # Request size category

        # Node states with new features
        for node in nodes:
            node_state = []

            # Node on/off state
            node_state.append(f"{'1' if node.state else '0'}")

            # Remaining battery energy categorization
            if node.battery_capacity == -1:
                battery_cat = "i"  # infinite
            else:
                remaining_energy = node.battery_capacity - node.energy_consumed
                if remaining_energy < 100:
                    battery_cat = "l"  # low
                elif remaining_energy < 1000:
                    battery_cat = "m"  # medium
                else:
                    battery_cat = "h"  # high
            # node_state.append(f"{battery_cat}")

            # processing queue (% of request size)
            processing_queue_size = np.sum(
                [request.size for request in node.processing_queue]
            )

            estimated_processing_time = node.estimated_processing_time(request)

            path_time = self.network.get_network_delay(
                request, self.network.generate_request_path(request.current_node, node)
            )
            estimated_time_to_complete = path_time + estimated_processing_time

            processing_time_buffer = estimated_time_to_complete - (
                request.qos_limit * request.tick_time
            )
            discretized_processing_time_buffer = 0
            if processing_time_buffer < 0.05:
                discretized_processing_time_buffer = 0
            elif processing_time_buffer < 0.1:
                discretized_processing_time_buffer = 1
            elif processing_time_buffer < 0.2:
                discretized_processing_time_buffer = 2
            else:
                discretized_processing_time_buffer = 3
            # node_state.append(f"{discretized_processing_time_buffer}")

            # Can process check
            can_process = (
                "1"
                if node.can_process(request, check_state=False, network_delay=path_time)
                else "0"
            )
            node_state.append(f"{can_process}")

            # Processing power category (in J/Mbit)
            processing_time = (
                request.size * node.cycle_per_bit / node.processing_frequency
            )
            processing_energy = node.processing_energy() * processing_time

            processing_power = processing_energy / request.size
            processing_power = processing_power * 1e6
            discretized_power = 0
            if processing_power < 2:
                discretized_power = 0
            elif processing_power < 5:
                discretized_power = 1
            elif processing_power < 10:
                discretized_power = 2
            else:
                discretized_power = 3
            node_state.append(f"{discretized_power}")

            # Add the discretized request size
            discretized_request_size = 0
            if request.size > 3e6:
                discretized_request_size = 2
            elif request.size > 6e6:
                discretized_request_size = 1
            else:
                discretized_request_size = 0
            node_state.append(f"{discretized_request_size}")

            state_parts.append("_".join(node_state))

        return "|".join(state_parts)

    def get_q_values(self, state: str, num_actions: int) -> np.ndarray:
        """Get Q-values for a state, initializing if needed"""
        if state not in self.q_table:
            self.q_table[state] = np.zeros(num_actions)
        return self.q_table[state]

    def select_compute_node(
        self, request: Request, nodes: List[BaseNode]
    ) -> tuple[BaseNode, List[BaseNode], float]:
        # Process any completed requests first
        self.process_completed_requests(nodes)

        state = self.get_state(request, nodes)
        q_values = self.get_q_values(state, len(nodes))

        # Epsilon-greedy action selection
        valid_actions = list(range(len(nodes)))
        if not valid_actions:
            raise ValueError("No valid nodes available for assignment")

        if np.random.random() < self.epsilon:
            action = np.random.choice(valid_actions)
        else:
            # print(f"state: {state}")
            # print(f"q_values: {q_values}")
            action = np.argmax(q_values)
            # print(f"action: {action}")

        # Store the request, state and action for later processing
        self.pending_requests[request.id] = {
            "state": state,
            "action": action,
            "request": request,
            "selected_node": nodes[action],
        }

        self.all_requests[request.id] = {
            "state": state,
            "action": action,
            "request": request,
            "selected_node": nodes[action],
            "nodes": nodes,
        }

        selected_node = nodes[action]
        path = self.network.generate_request_path(request.current_node, selected_node)
        total_delay = self.network.get_network_delay(request, path)

        if self.debug:
            print(f"Q values: {q_values}, for state {state}")
            print(f"Selected node {action} with Q-values: {q_values}")

        return selected_node, path, total_delay

    def process_completed_requests(self, nodes: List[BaseNode]):
        """Process completed or failed requests and update Q-values"""
        completed_requests = []

        for request_id, info in self.pending_requests.items():
            request = info["request"]

            # Check if request is completed or failed
            if request.status in [RequestStatus.COMPLETED, RequestStatus.FAILED]:
                selected_node = info["selected_node"]

                # Calculate immediate reward for this request
                if request.status == RequestStatus.FAILED:
                    reward = -1000.0
                else:
                    # Get energy consumption between start and end time
                    desired_tick = 0
                    desired_tick_status = RequestStatus.PROCESSING
                    for status in request.status_history:
                        if status[0] == desired_tick_status:
                            desired_tick = status[1]
                            break

                    start_time = desired_tick
                    end_time = request.last_status_change
                    energy_consumption = np.sum(
                        selected_node.energy_history[start_time:end_time]
                    )

                    # Calculate energy per Mbit
                    energy_per_mbit = (energy_consumption / request.size) * 1e6
                    reward = -energy_per_mbit

                # Update Q-values
                state = info["state"]
                action = info["action"]

                if self.debug:
                    print(f"state: {state}")
                    print(f"reward: {reward}")

                old_value = self.q_table[state][action]
                new_value = (1 - self.alpha) * old_value + self.alpha * reward
                self.q_table[state][action] = new_value

                completed_requests.append(request_id)

        # Remove processed requests
        for request_id in completed_requests:
            del self.pending_requests[request_id]

    def apply_episode_reward(self, episode_reward: float, qos_score: float):
        """Apply episode-level reward to all states visited in this episode"""
        # Get all states visited in this episode, ordered by timestamp
        episode_states = []
        for request_id, info in self.all_requests.items():
            request = info["request"]
            nodes = info["nodes"]
            state = info["state"]
            episode_states.append((request_id, state, info["action"], request))

        # If QoS is bad, apply penalties to all states that led to this outcome
        if qos_score < 95:
            penalty = -100000.0 * (1 - qos_score / 100)  # Large penalty for bad QoS
            for _, state, action, request in episode_states:
                if request.status == RequestStatus.FAILED:
                    old_value = self.q_table[state][action]
                    new_value = (1 - self.alpha) * old_value + self.alpha * penalty
                    self.q_table[state][action] = new_value

    def save_qtable(self, path: str):
        """Save Q-table to file"""
        with open(path, "wb") as f:
            pickle.dump(self.q_table, f)

    def calculate_request_reward(
        self, request: Request, selected_node: BaseNode
    ) -> float:
        """Calculate reward for a single request completion"""
        if request.status == RequestStatus.FAILED:
            return -1000.0  # Penalty for failure

        if request.status == RequestStatus.COMPLETED:
            # Calculate energy efficiency
            processing_time = (
                request.size
                * selected_node.cycle_per_bit
                / selected_node.processing_frequency
            )
            energy_consumed = (
                selected_node.processing_energy() * processing_time
            ) / 1000  # Convert to kJ

            # Combine metrics
            reward = 50.0
            reward -= energy_consumed  # Energy penalty (scaled)

            return reward

        return -10.0  # encourage quick processing
