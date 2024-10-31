from optimisation_ntn.utils.type import Position

from .base_node import BaseNode
from ..utils.type import Position


class BaseStation(BaseNode):
    def __init__(self, node_id: int, initial_position: Position):
        super().__init__(node_id, initial_position)
        self.state = False

    def turn_on(self):
        self.state = True

    def turn_off(self):
        self.state = False

    def __str__(self):
        return f"Base Station {self.node_id}"
