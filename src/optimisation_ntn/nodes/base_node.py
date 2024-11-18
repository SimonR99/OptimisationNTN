from abc import ABC
from typing import Dict, List, Optional, Tuple

from optimisation_ntn.utils.earth import Earth

from ..networks.antenna import Antenna
from ..networks.request import Request, RequestStatus
from ..utils.position import Position


class BaseNode(ABC):
    def __init__(
        self,
        node_id: int,
        initial_position: Position,
        temperature=300,
        debug: bool = False,
    ):
        self.node_id = node_id
        self.position = initial_position
        self.state = False
        self.antennas: List[Antenna] = []
        self.temperature = temperature
        self.active_links: Dict[Tuple[type, type], int] = (
            {}
        )  # Track active links by node type pair
        self.current_load = 0.0
        self.processing_power = 0.0
        self.processing_queue: List[Request] = []
        self.debug = debug

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
        """Turn node on"""
        self.state = True

    def turn_off(self):
        """Turn node off"""
        self.state = False

    def __str__(self):
        return f"Node {self.node_id}"

    def can_process(self, request: Request) -> bool:
        return (
            self.state
            and self.processing_power > 0
            and self.current_load + request.cycle_bits <= self.processing_power
        )

    def add_request_to_process(self, request: Request):
        """Add request to processing queue"""
        if self.can_process(request):
            self.processing_queue.append(request)
            self.current_load += request.cycle_bits
            request.status = RequestStatus.PROCESSING
            request.current_node = self
            request.processing_progress = 0
            self.debug_print(
                f"Request {request.id} status changed to {request.status.name} at {self}"
            )
        else:
            self.debug_print(
                f"Node {self} cannot process request {request.id} (current load: {self.current_load}, power: {self.processing_power})"
            )

    def process_requests(self, time: float):
        """Process requests in queue"""
        if not self.processing_queue:
            return

        # Process each request in queue
        completed = []
        for request in self.processing_queue:
            request.processing_progress += self.processing_power * time
            self.debug_print(
                f"Node {self}: Processing request {request.id} "
                f"({request.processing_progress:.1f}/{request.cycle_bits} units)"
            )

            if request.processing_progress >= request.cycle_bits:
                completed.append(request)
                self.current_load -= request.cycle_bits
                request.status = RequestStatus.COMPLETED
                request.satisfaction = True
                self.debug_print(
                    f"Request {request.id} status changed to {request.status.name} at {self}"
                )

        # Remove completed requests
        for request in completed:
            self.processing_queue.remove(request)

    def tick(self, time: float):
        """Update node state including request processing"""
        self.process_requests(time)

    def debug_print(self, *args, **kwargs):
        """Print only if debug mode is enabled"""
        if self.debug:
            print(*args, **kwargs)
