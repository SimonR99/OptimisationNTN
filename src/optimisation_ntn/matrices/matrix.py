import numpy as np
from typing import Optional

class Matrix:
    def __init__(self, rows: int, cols: int, name: str):
        self.data = np.zeros((rows, cols))
        self.name = name

    def update(self, data: np.ndarray):
        self.data = data

    def get_value(self, i: int, j: int) -> float:
        return self.data[i, j]

    def set_value(self, i: int, j: int, value: float):
        self.data[i, j] = value

    def apply_mask(self, mask: np.ndarray):
        """Apply a mask to the matrix with element-wise multiplication."""
        if mask.shape != self.data.shape:
            raise ValueError(f"Mask shape mismatch: expected {self.data.shape}, got {mask.shape}")

        np.multiply(self.data, mask, out=self.data)

    def get_rows(self) -> int:
        """Get number of rows in matrix."""
        return self.data.shape[0]

    def get_cols(self) -> int:
        """Get number of columns in matrix."""
        return self.data.shape[1]