from abc import ABC
from typing import Dict, List, Optional, Tuple

from optimisation_ntn.utils.earth import Earth

from ..networks.antenna import Antenna
from ..networks.request import Request, RequestStatus
from ..utils.position import Position


def transmission_delay(request: Request, link_bandwidth):
    return request.size / link_bandwidth


def convert_dbm_watt(transmission_power) -> float:
    """Convert signal_power from dBm to Watt."""
    return (10 ** (transmission_power / 10)) / 1000


class BaseNode(ABC):
    def __init__(
        self,
        node_id: int,
        initial_position: Position,
        debug: bool = False,
    ):
        self.node_id = node_id
        self.position = initial_position
        self.state = False
        self.antennas: List[Antenna] = []
        self.active_links: Dict[Tuple[type, type], int] = (
            {}
        )  # Track active links by node type pair
        self.current_load = 0.0
        self.cycle_per_bit = 500  # 500 cycles per each bit
        self.processing_queue: List[Request] = []
        self.battery_capacity = 0
        self.energy_consumed = 0.0
        self.processing_frequency = 0
        self.transmission_power = 0
        self.k_const = 0
        """Défini dans des études"""
        self.spectral_noise_density = -174
        """Ce peak d'énergie est une constante déterminée sans sources scientifiques."""
        self.turn_on_energy_peak = 0.03
        self.turn_on_standby_energy = 0.01
        self.recently_turned_on = False
        self.debug = debug
        self.name = ""
        self.path_loss_exponent = 0.0
        self.attenuation_coefficient = 0.0
        self.reference_lenght = 0.0
        self.destinations: List["BaseNode"] = []

    def get_name(self) -> str:
        return self.name

    def add_antenna(self, antenna_type: str, gain: float):
        """Adds an antenna with a specified type and gain to the node."""
        self.antennas.append(Antenna(antenna_type, gain))

    def get_compatible_antenna(self, other_antenna: Antenna) -> Optional[Antenna]:
        """Finds a compatible antenna for communication based on type."""
        for antenna in self.antennas:
            if antenna.is_compatible_with(other_antenna):
                return antenna
        return None

    def add_destination(self, destination: "BaseNode"):
        """Add a destination node to the node"""
        self.destinations.append(destination)

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

    def processing_time(self, request: Request) -> float:
        """Calculate processing time for a request"""
        total_load = self.current_load + request.size
        return self.cycle_per_bit * total_load / self.processing_frequency

    def turn_on(self):
        """Turn node on and add energy consumed."""

        if self.battery_capacity <= 0:
            return
        self.energy_consumed += self.turn_on_energy_peak
        self.state = True
        self.recently_turned_on = True

    def turn_off(self):
        """Turn node off"""
        self.state = False

    def __str__(self):
        return f"Node {self.node_id}"

    def can_process(
        self, request: Request | None = None, check_state: bool = True
    ) -> bool:
        """Check if node can process a request

        Args:
            request: The request to process. If None, checks basic processing capability.
            check_state: Whether to check if the node is on or not
        Returns:
            bool: True if the node can process the request, False otherwise.
        """
        # Basic checks for processing capability
        if self.processing_frequency <= 0:
            return False

        if check_state and not self.state:
            return False

        # If no specific request, just check basic capability
        if request is None:
            return True

        # Calculate processing time for the new total load
        return self.processing_time(request) <= request.qos_limit

    def add_request_to_process(self, request: Request):
        """Add request to processing queue"""
        if self.can_process(request):
            self.processing_queue.append(request)
            self.current_load += request.size
            request.status = RequestStatus.PROCESSING
            request.current_node = self
            request.processing_progress = 0
            self.debug_print(
                f"Request {request.id} status changed to {request.status.name} at {self}"
            )
        else:
            self.debug_print(
                f"Node {self} cannot process request {request.id} (current load: {self.current_load}, power: {self.processing_frequency})"
            )

    def process_requests(self, time: float):
        """Process requests in queue"""
        if not self.processing_queue:
            return

        # Process each request in queue
        completed = []
        for request in self.processing_queue:
            request.processing_progress += (
                self.processing_frequency * time / self.cycle_per_bit
            )
            self.energy_consumed += self.processing_energy() * time

            self.debug_print(
                f"Node {self}: Processing request {request.id} "
                f"({request.processing_progress:.1f}/{request.size} units)\n"
                f"Energy consumed up to now: {self.energy_consumed:.1f} joules"
            )

            if request.processing_progress >= request.size:
                request.update_status(RequestStatus.COMPLETED)
                request.satisfaction = True
                completed.append(request)
                self.current_load -= request.size
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

    def transmission_energy(self, request: Request, link_bandwidth: float):
        """Calculates the transmission energy consumed from the haps to the next node (bs or Leo) and turns off the node
        if the battery is depleted.
        :param link_bandwidth:
        :param request:
        :return: energy consumed in joules
        """
        # transmission power has to go from dBm to Watt
        transmission_energy = convert_dbm_watt(
            self.transmission_power
        ) * transmission_delay(request, link_bandwidth)
        self.battery_capacity -= transmission_energy
        if self.battery_capacity <= 0 and self.get_name() != "BS":
            self.turn_off()
        return transmission_energy

    def processing_delay(self, request: Request):
        return (request.size * 1000) / self.processing_frequency

    def processing_energy(self):
        """Calculates the processing energy consumed and turn off the node if the battery is depleted.
        :return: energy consumed in joules
        """
        processing_energy = (
            self.k_const
            * (self.processing_frequency**3)
            * self.processing_delay(self.processing_queue[0])
        )
        self.battery_capacity -= processing_energy
        if self.battery_capacity <= 0 and self.get_name() != "BS":
            self.turn_off()
        return processing_energy

    def consume_standby_energy(self):
        if self.state:
            self.energy_consumed += self.turn_on_standby_energy
            if self.battery_capacity <= 0 and self.get_name() != "BS":
                self.turn_off()
