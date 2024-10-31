class Request:
    def __init__(self, req_id: int, priority: int, qos: float, size: int, cycle_bits):
        self.req_id = req_id
        self.priority = priority
        self.qos = qos
        self.size = size
        self.cycle_bits = cycle_bits

