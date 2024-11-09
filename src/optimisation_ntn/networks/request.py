import random
from enum import Enum


class RequestStatus(Enum):
    CREATED = 0
    IN_TRANSIT = 1
    IN_PROCESSING_QUEUE = 2
    PROCESSING = 3
    COMPLETED = 4


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Request:
    lamda = 0
    size = 0
    cycle_bits = 0
    id = 0
    priority = random.randint(1, 3)

    def __init__(self, tick: int, initial_node: "BaseNode", target_node: "BaseNode"):
        self.id = 0
        self.tick = tick  # time of appearance
        self.current_node = initial_node
        self.target_node = target_node
        self.status = RequestStatus.CREATED
        self.satisfaction = False

        self.qos_limit = 0.0
        self.set_priority_type(self.priority)

    def set_id(self, row: int, col: int):
        self.id = int(f"{row}{col}")

    def get_id(self):
        return self.id

    def set_size(self, size: int):
        self.size = size

    def set_priority_type(self, priority):
        match priority:
            case Priority.HIGH:
                self.lamda = 0.2
                self.qos_limit = 0.1  # 100 ms
                self.size = random.randint(1, 3)
                self.cycle_bits = random.randint(100, 130)
            case Priority.MEDIUM:
                self.lamda = 0.5
                self.qos_limit = 0.3  # 300 ms
                self.size = random.randint(4, 6)
                self.cycle_bits = random.randint(131, 160)
            case Priority.LOW:
                self.lamda = 1
                self.qos_limit = 0.5  # 500 ms
                self.size = random.randint(7, 10)
                self.cycle_bits = random.randint(161, 200)

    def is_satisfied(self):
        return self.satisfaction

    def __str__(self):
        return f"Priority: {self.priority} + \nAppearing time: {self.tick} + \nSatisfaction:{self.satisfaction}"
