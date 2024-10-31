from abc import ABC

from ..utils.type import Position


class BaseNode(ABC):

    def __init__(self, node_id: int, initial_position: Position | None = None):
        self.node_id = node_id
        self.position = initial_position
        self.state = False

    def turn_on(self):
        self.state = True

    def turn_off(self):
        self.state = False

    def __str__(self):
        return f"Node {self.node_id}"

    def tick(self, time):
        pass
