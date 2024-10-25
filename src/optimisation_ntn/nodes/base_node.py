from abc import ABC

from optimisation_ntn.utils.type import Position


class BaseNode(ABC):
    def __init__(self, node_id: int, initial_position: Position):
        self.node_id = node_id
        self.position = initial_position
        self.state = "on"

    def turn_on(self):
        self.state = "on"

    def turn_off(self):
        self.state = "off"

    def __str__(self):
        return f"Node {self.node_id}"

    def tick(self, time):
        pass
