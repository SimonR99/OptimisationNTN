from optimisation_ntn.utils.type import Position
from optimisation_ntn.users.request import Request

class Device:

    def __init__(self, user_id: int, initial_position: Position, request: Request):
        self.user_id = user_id
        self.position = initial_position
        self.request = request