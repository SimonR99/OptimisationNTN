from abc import ABC


class BaseNode(ABC):
    def __init__(self, node_id):
        self.node_id = node_id
        self.state = "on"

    def turn_on(self):
        self.state = "on"

    def turn_off(self):
        self.state = "off"

    def __str__(self):
        return f"Node {self.node_id}"
