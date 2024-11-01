from optimisation_ntn.utils.earth import Earth
from optimisation_ntn.utils.type import Position

from .base_node import BaseNode


class UserDevice(BaseNode):

    def __init__(self, node_id: int, initial_position: Position):
        super().__init__(node_id, initial_position)

    def __str__(self):
        return f"User {self.node_id}"
