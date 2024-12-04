def convert_dbm_watt(transmission_power) -> float:
    """Convert signal_power from dBm to Watt."""
    return (10 ** (transmission_power / 10)) / 1000
