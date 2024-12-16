""" User device class """

from typing import Literal

from optimisation_ntn.networks.request import Request
from optimisation_ntn.utils.position import Position

from .base_node import BaseNode


class UserDevice(BaseNode):
    """User device class"""

    REQUEST_LIMIT = 1

    def __init__(
        self,
        node_id: int,
        initial_position: Position,
        debug: bool = False,
    ):
        super().__init__(
            node_id, initial_position, debug=debug
        )
        self.add_antenna("VHF", 3)
        self.transmission_power = 23
        self.path_loss_exponent = 3
        self.attenuation_coefficient = 3
        self.current_requests: list[Request] = []
        self.name = "USER DEVICE"
        self.idle_energy = 0
        self.turn_on_energy_peak = 0

    def add_request(self, request) -> Request:
        """Create a new request without specifying target node yet"""
        self.current_requests.append(request)
        self.debug_print(
            f"User {self.node_id} created request {request.id} with status {request.status}"
        )
        return request

    def assign_target_node(self, request: Request, target_node: BaseNode):
        """Assign a target node to an existing request"""
        request.target_node = target_node
        self.debug_print(f"Request {request.id} assigned target node: {target_node}")

    def __str__(self):
        return f"User {self.node_id}"
