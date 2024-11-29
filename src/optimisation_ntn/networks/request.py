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
    FAILED = 5


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Request:
    id_counter = 0

    def __init__(
        self,
        tick: int,
        initial_node: "BaseNode",
        target_node: Optional["BaseNode"] = None,
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
                self.qos_limit = 0.2  # 200 ms
                self.size = random.randint(5, 15) * 1000  # 5 to 15 kilo bytes
            case Priority.MEDIUM:
                self.qos_limit = 0.5  # 500 ms
                self.size = random.randint(10, 40) * 1000  # 10 to 40 kilo bytes
            case Priority.LOW:
                self.qos_limit = 1  # 1000 ms
                self.size = random.randint(30, 50) * 1000  # 30 to 50 kilo bytes
        self.debug_print(
            f"Request {self.id} created with size {self.size / 1000} kilo bytes"
        )

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
