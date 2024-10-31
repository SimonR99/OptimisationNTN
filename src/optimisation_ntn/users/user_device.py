from optimisation_ntn.utils.type import Position
from optimisation_ntn.users.request import Request

class Device:
    def __init__(self, node_id: int, initial_position: Position, request: Request):
        self.node_id = node_id
        self.position = initial_position
        self.request = request
