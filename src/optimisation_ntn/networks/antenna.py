from typing import Type


class Antenna:
    def __init__(self, antenna_type: str, gain: float, height: float) :
        self.antenna_type = antenna_type  # Type of the antenna (e.g., "UHF", "VHF")
        self.gain = gain  # Gain of the antenna
        self.height = height  # Height of the antenna

    def is_compatible_with(self, other: "Antenna") -> bool:
        """Checks if this antenna can communicate with the other based on type."""
        return self.antenna_type == other.antenna_type
