class Position:
    """A simple class to represent a 2D position."""

    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def distance_to(self, other: "Position") -> float:
        """Calculate the Euclidean distance between two Position instances."""
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5

    def __str__(self):
        return f"Position(x={self.x}, y={self.y})"

    @staticmethod
    def distance(p1: "Position", p2: "Position") -> float:
        """Calculate the Euclidean distance between two Position instances."""
        return ((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2) ** 0.5
