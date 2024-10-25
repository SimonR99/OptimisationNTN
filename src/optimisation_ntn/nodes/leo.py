from .base_node import BaseNode


class LEO(BaseNode):

    leo_altitude = 500e3

    earth_mass = 5.972e24
    earth_radius = 6.371e6
    gravitational_constant = 6.67430e-11

    def __init__(self, node_id):
        super().__init__(node_id)
        self.state = "off"
        self.battery_capacity = 100

    @property
    def speed(self):
        return (
            self.gravitational_constant
            * self.earth_mass
            / (self.earth_radius + self.leo_altitude)
        ) ** 0.5

    def turn_on(self):
        self.state = "on"

    def turn_off(self):
        self.state = "off"

    def __str__(self):
        return f"LEO {self.node_id}"
