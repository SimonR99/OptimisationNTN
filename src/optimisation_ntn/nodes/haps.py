from .base_node import BaseNode


class HAPS(BaseNode):
    def __init__(self, node_id):
        super().__init__(node_id)
        self.state = "off"
        self.battery_capacity = 1000

    def turn_on(self):
        self.state = "on"

    def turn_off(self):
        self.state = "off"

    def __str__(self):
        return f"HAPS {self.node_id}"
