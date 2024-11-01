import numpy as np
from typing import Optional

class Matrix:
    def __init__(self, rows: int, cols: int, name: str):
        self.data = np.zeros((rows, cols))
        self.name = name

    def update(self, data: np.ndarray):
        if data.shape == self.data.shape:
            self.data = data.copy()
        else:
            raise ValueError(f"Shape mismatch: expected {self.data.shape}, got {data.shape}")

    def get_value(self, i: int, j: int) -> float:
        return self.data[i, j]

    def set_value(self, i: int, j: int, value: float):
        self.data[i, j] = value

    def apply_mask(self, mask: np.ndarray):
        if mask.shape == self.data.shape:
            self.data = self.data * mask
        else:
            raise ValueError(f"Mask shape mismatch: expected {self.data.shape}, got {mask.shape}") 