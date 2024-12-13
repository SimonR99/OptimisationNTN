""" Position class """

import numpy as np


class Position:
    """A position class using numpy arrays."""

    def __init__(self, x: float, y: float):
        self.coords = np.array([x, y], dtype=float)

    @property
    def x(self) -> float:
        """X coordinate"""
        return self.coords[0]

    @property
    def y(self) -> float:
        """Y coordinate"""
        return self.coords[1]

    def distance_to(self, other: "Position") -> float:
        """Calculate distance using numpy operations."""
        return np.sqrt(np.sum((self.coords - other.coords) ** 2))

    def __str__(self):
        return f"Position(x={self.x}, y={self.y})"

    @staticmethod
    def distances(positions: list["Position"]) -> np.ndarray:
        """Calculate distances between all positions efficiently."""
        coords = np.array([p.coords for p in positions])
        return np.sqrt(np.sum((coords[:, np.newaxis] - coords) ** 2, axis=2))
