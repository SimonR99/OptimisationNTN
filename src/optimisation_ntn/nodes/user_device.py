from multiprocessing import set_forkserver_preload

from optimisation_ntn.networks.request import Request, RequestStatus
from optimisation_ntn.utils.earth import Earth
from optimisation_ntn.utils.position import Position

from ..networks.antenna import Antenna
from .base_node import BaseNode


class UserDevice(BaseNode):
    REQUEST_LIMIT = 1

    def __init__(self, node_id: int, initial_position: Position, debug: bool = False):
        super().__init__(node_id, initial_position, debug=debug)
        self.add_antenna("VHF", 3)
        self.transmission_power = 23
        self.path_loss_exponent = 3
        self.attenuation_coefficient = 3
        self.reference_lenght = 1
        self.current_requests: list[Request] = []
        self.transmission_power = 23
        self.name = "USER DEVICE"

    def create_request(self, tick: int) -> Request:
        """Create a new request without specifying target node yet"""
        request = Request(tick, self, None, debug=self.debug)
        self.current_requests.append(request)
        self.debug_print(
            f"User {self.node_id} created request {request.id} with status {request.status.name}"
        )
        return request

    def assign_target_node(self, request: Request, target_node: BaseNode):
        """Assign a target node to an existing request"""
        request.target_node = target_node
        self.debug_print(f"Request {request.id} assigned target node: {target_node}")

    def __str__(self):
        return f"User {self.node_id}"
