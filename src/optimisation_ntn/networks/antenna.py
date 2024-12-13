""" Antenna class """


class Antenna:
    """Antenna class"""

    def __init__(self, antenna_type: str, gain: float):
        self.antenna_type = antenna_type  # Type of the antenna (e.g., "UHF", "VHF")
        self.gain = gain  # Gain of the antenna

    def is_compatible_with(self, other: "Antenna") -> bool:
        """Checks if this antenna can communicate with the other based on type."""
        return self.antenna_type == other.antenna_type

    def __str__(self):
        return f"Antenna(type={self.antenna_type}, gain={self.gain})"
