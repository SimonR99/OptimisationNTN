from abc import ABC
from typing import Dict, List, Optional, Tuple

from optimisation_ntn.utils.earth import Earth

from ..networks.antenna import Antenna
from ..utils.type import Position


class BaseNode(ABC):
    def __init__(
        self, node_id: int, initial_position: Position | None = None, temperature=300
    ):
        self.node_id = node_id
        self.position = initial_position
        self.state = False
        self.antennas: List[Antenna] = []
        self.temperature = temperature
        self.active_links: Dict[Tuple[type, type], int] = (
            {}
        )  # Track active links by node type pair

    def add_antenna(self, antenna_type: str, gain: float):
        """Adds an antenna with a specified type and gain to the node."""
        self.antennas.append(Antenna(antenna_type, gain))

    def get_compatible_antenna(self, other_antenna: Antenna) -> Optional[Antenna]:
        """Finds a compatible antenna for communication based on type."""
        for antenna in self.antennas:
            if antenna.is_compatible_with(other_antenna):
                return antenna
        return None

    def get_active_count(self, other_node_type: type) -> int:
        """Returns active link count for a given node type."""
        link_type = (type(self), other_node_type)
        return self.active_links.get(link_type, 0)

    def add_active_link(self, other_node_type: type):
        """Increments active link count for a given node type."""
        link_type = (type(self), other_node_type)
        if link_type not in self.active_links:
            self.active_links[link_type] = 0
        self.active_links[link_type] += 1

    def remove_active_link(self, other_node_type: type):
        """Decrements active link count for a given node type."""
        link_type = (type(self), other_node_type)
        if link_type in self.active_links and self.active_links[link_type] > 0:
            self.active_links[link_type] -= 1

    @property
    def spectral_noise_density(self) -> float:
        """Calculates spectral noise density based on temperature."""
        return Earth.bolztmann_constant * self.temperature

    def turn_on(self):
        self.state = True

    def turn_off(self):
        self.state = False

    def __str__(self):
        return f"Node {self.node_id}"

    def tick(self, time):
        pass
