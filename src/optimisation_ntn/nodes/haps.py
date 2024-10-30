from .base_node import BaseNode
from ..utils.type import Position


class Haps(BaseNode):
    def __init__(self, node_id: int, initial_position: Position):
        super().__init__(node_id, initial_position)
        self.state = False
        self.battery_capacity = 1000

    def turn_on(self):
        self.state = True

    def turn_off(self):
        self.state = False

    def __str__(self):
        return f"HAPS {self.node_id}"
