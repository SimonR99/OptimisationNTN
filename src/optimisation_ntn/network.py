from .nodes.haps import HAPS


class Network:
    def __init__(self):
        self.nodes = []
        self.communication_links = []

    def tick(self):
        for node in self.nodes:
            node.tick()
