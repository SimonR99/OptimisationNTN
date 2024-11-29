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
        self.add_antenna("VHF", 1.5)
        self.current_requests: list[Request] = []
        self.transmission_power = 23
        self.name = "USER DEVICE"

    def spawn_request(self, tick: int, target_node: BaseNode) -> Request:
        """Spawn a new request from this user device"""
        request = Request(tick, self, target_node, debug=self.debug)
        request.status = RequestStatus.CREATED
        self.current_requests.append(request)
        self.debug_print(
            f"User {self.node_id} spawned request {request.id} with status {request.status.name}"
        )
        return request

    def __str__(self):
        return f"User {self.node_id}"
