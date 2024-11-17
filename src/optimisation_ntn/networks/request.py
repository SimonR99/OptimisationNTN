import random
import time
from enum import Enum
from typing import List, Optional, Tuple


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
    id_counter = 0

    def __init__(
        self,
        tick: int,
        initial_node: "BaseNode",
        target_node: "BaseNode",
        debug: bool = False,
    ):
        self.debug = debug

        self.id = Request.id_counter
        Request.id_counter += 1
        self.tick = tick
        self.current_node = initial_node
        self.next_node = None
        self.target_node = target_node
        self.status = RequestStatus.CREATED
        self.satisfaction = False
        self.processing_progress: float = 0.0
        self.qos_limit = 0.0
        self.size = 0.0
        self.cycle_bits = 0.0
        self.priority = random.choice(list(Priority))
        self.creation_time = tick
        self.last_status_change = tick
        self.status_history: List[Tuple[RequestStatus, float]] = [
            (RequestStatus.CREATED, float(tick))
        ]
        self.path: Optional[List["BaseNode"]] = None
        self.path_index = 0

        self.set_priority_type(self.priority)

    def debug_print(self, *args, **kwargs):
        """Print only if debug mode is enabled"""
        if self.debug:
            print(*args, **kwargs)

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
                self.size = random.randint(10, 30) * 500
                self.cycle_bits = random.randint(10, 30)
            case Priority.MEDIUM:
                self.lamda = 0.5
                self.qos_limit = 0.3  # 300 ms
                self.size = random.randint(20, 40) * 500
                self.cycle_bits = random.randint(20, 40)
            case Priority.LOW:
                self.lamda = 1
                self.qos_limit = 0.5  # 500 ms
                self.size = random.randint(30, 50) * 500
                self.cycle_bits = random.randint(30, 50)
        self.debug_print(f"Request {self.id} created with size {self.size} bits")

    def is_satisfied(self):
        return self.satisfaction

    def __str__(self):
        return f"Priority: {self.priority} + \nAppearing time: {self.tick} + \nSatisfaction:{self.satisfaction}"

    @property
    def time_in_current_status(self):
        return time.time() - self.last_status_change

    @property
    def total_time(self):
        return time.time() - self.creation_time

    def update_status(self, new_status: RequestStatus):
        """Update request status and track timing"""
        current_time = time.time()
        self.status_history.append((new_status, current_time))
        self.debug_print(
            f"Request {self.id} status changed: {self.status} -> {new_status} "
            f"(time in previous status: {current_time - self.last_status_change:.2f}s)"
        )
        self.status = new_status
        self.last_status_change = current_time
