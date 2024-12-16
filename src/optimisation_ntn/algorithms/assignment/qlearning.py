"""Q-learning based assignment strategy"""

from typing import List, Dict, Tuple
import numpy as np

from ...networks.request import Request
from ...nodes.base_node import BaseNode
from .assignment_strategy import AssignmentStrategy


class QLearningAssignment(AssignmentStrategy):
    """Assigns requests using Q-learning"""

    def __init__(
        self,
        network,
        learning_rate=0.1,
        discount_factor=0.95,
        epsilon_start=0.9,
        epsilon_end=0.05,
    ):
        self.network = network
        self.q_table: Dict[Tuple, np.ndarray] = {}  # State -> Action values
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon = epsilon_start
        self.last_state = None
        self.last_action = None
        self.episodes_seen = 0  # Track number of episodes for epsilon decay

    def _discretize_energy(self, energy: float) -> int:
        """Discretize energy levels into buckets"""
        if energy == -1:
            return 0
        elif energy <= 200:
            return 1
        elif energy <= 1000:
            return 2
        else:
            return 3

    def _discretize_size(self, size: float) -> int:
        """Discretize request size into buckets"""
        if size <= 3e6:
            return 0
        elif size <= 6e6:
            return 1
        elif size <= 10e6:
            return 2
        else:
            return 3

    def _get_state(self, request: Request, nodes: List[BaseNode]) -> Tuple:
        """Create state tuple from current system state"""
        # Get energy levels for each compute node
        energy_states = tuple(
            self._discretize_energy(
                -1
                if node.battery_capacity == -1
                else node.battery_capacity - node.energy_consumed
            )
            for node in nodes
        )

        # Get node states (on/off)
        node_states = tuple(int(node.state) for node in nodes)

        # Get request size state
        size_state = self._discretize_size(request.size)

        return energy_states + node_states + (size_state,)

    def update_q_value(self, reward: float, new_state: Tuple = None):
        """Update Q-value based on reward and new state"""
        if self.last_state is None or self.last_action is None:
            return

        # Initialize Q-values for states if they don't exist
        if self.last_state not in self.q_table:
            self.q_table[self.last_state] = np.zeros(len(self.network.compute_nodes))

        if new_state and new_state not in self.q_table:
            self.q_table[new_state] = np.zeros(len(self.network.compute_nodes))

        # Calculate new Q-value
        current_q = self.q_table[self.last_state][self.last_action]

        if new_state is None:
            # Terminal state
            new_q_value = reward
        else:
            # Get max Q-value for next state
            max_future_q = np.max(self.q_table[new_state])
            new_q_value = reward + self.discount_factor * max_future_q

        # Update Q-value with learning rate
        self.q_table[self.last_state][self.last_action] = (
            current_q + self.learning_rate * (new_q_value - current_q)
        )

        # Debug print to see Q-value updates
        print(
            f"Updating Q-value for state {self.last_state}, action {self.last_action}"
        )
        print(
            f"Old Q-value: {current_q:.4f}, New Q-value: {self.q_table[self.last_state][self.last_action]:.4f}"
        )

    def get_epsilon(self, episode: int, total_episodes: int) -> float:
        """Calculate epsilon using exponential decay"""
        # Exponential decay from epsilon_start to epsilon_end
        decay_rate = -np.log(self.epsilon_end / self.epsilon_start) / (
            total_episodes * 0.8
        )
        return self.epsilon_end + (self.epsilon_start - self.epsilon_end) * np.exp(
            -decay_rate * episode
        )

    def select_compute_node(
        self, request: Request, nodes: List[BaseNode]
    ) -> tuple[BaseNode, List[BaseNode], float]:
        new_state = self._get_state(request, nodes)

        # Initialize Q-values for new state
        if new_state not in self.q_table:
            self.q_table[new_state] = np.zeros(len(nodes))

        # Epsilon-greedy action selection with current epsilon value
        if np.random.random() < self.epsilon:
            action = np.random.randint(len(nodes))
        else:
            action = np.argmax(self.q_table[new_state])

        # Store state and action for next update
        self.last_state = new_state
        self.last_action = action

        selected_node = nodes[action]
        path = self.network.generate_request_path(request.current_node, selected_node)
        total_delay = self.network.get_network_delay(request, path)

        return selected_node, path, total_delay

    def reset(self):
        """Reset episode-specific variables but keep Q-table"""
        self.last_state = None
        self.last_action = None
        self.episodes_seen += 1  # Increment episode counter

    def save_q_table(self, filename: str):
        """Save Q-table to file"""
        np.save(filename, self.q_table)

    def load_q_table(self, filename: str):
        """Load Q-table from file"""
        self.q_table = np.load(filename, allow_pickle=True).item()

    def interpret_state(self, state: Tuple) -> str:
        """Interpret a state tuple in human-readable format"""
        num_nodes = len(self.network.compute_nodes)
        energy_states = state[:num_nodes]
        node_states = state[num_nodes : 2 * num_nodes]
        size_state = state[-1]

        energy_meanings = ["Infinite", "Depleted", "Low", "High"]
        size_meanings = ["≤3MB", "≤6MB", "≤10MB", ">10MB"]

        interpretation = "State interpretation:\n"
        interpretation += "\nNode Energy Levels:\n"
        for i, energy in enumerate(energy_states):
            interpretation += f"Node {i}: {energy_meanings[energy]}\n"

        interpretation += "\nNode States:\n"
        for i, state in enumerate(node_states):
            interpretation += f"Node {i}: {'On' if state else 'Off'}\n"

        interpretation += f"\nRequest Size: {size_meanings[size_state]}"

        if state in self.q_table:
            interpretation += "\n\nQ-values for each node:"
            for i, value in enumerate(self.q_table[state]):
                interpretation += f"\nNode {i}: {value:.4f}"

        return interpretation

    def print_q_table_summary(self):
        """Print a summary of the Q-table"""
        print(f"Q-table contains {len(self.q_table)} states")

        # Find state with highest Q-value
        max_q = float("-inf")
        best_state = None
        best_action = None

        for state, q_values in self.q_table.items():
            max_val = np.max(q_values)
            if max_val > max_q:
                max_q = max_val
                best_state = state
                best_action = np.argmax(q_values)

        if best_state:
            print("\nBest learned action:")
            print(self.interpret_state(best_state))
            print(f"\nBest action: Node {best_action}")
            print(f"Q-value: {max_q:.4f}")
