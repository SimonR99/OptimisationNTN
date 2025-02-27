"""Request module"""

import random
from enum import Enum
from typing import Callable, List, Optional, Tuple


class RequestStatus(Enum):
    """Request status"""

    CREATED = 0
    IN_TRANSIT = 1
    IN_PROCESSING_QUEUE = 2
    PROCESSING = 3
    COMPLETED = 4
    FAILED = 5


class Priority(Enum):
    """Request priority"""

    LOW = 1
    MEDIUM = 2
    HIGH = 3


# pylint: disable=R0902,R0913,R0917
class Request:
    """Request class"""

    id_counter = 0

    def __init__(
        self,
        tick: int,
        tick_time: float,
        initial_node: "BaseNode",
        get_tick: Callable[[], float],
        target_node: Optional["BaseNode"] = None,
        debug: bool = False,
    ):
        self.debug = debug
        self.id = Request.id_counter
        Request.id_counter += 1
        self.current_node = initial_node
        self.next_node: Optional["BaseNode"] = None
        self.target_node = target_node
        self.status = RequestStatus.CREATED
        self.processing_progress: float = 0.0  # bits
        self.qos_limit = 0.0  # seconds
        self.size = 0.0  # bits
        self.priority = random.choice(list(Priority))
        self.creation_time = tick
        self.last_status_change = tick
        self.status_history: List[Tuple[RequestStatus, float]] = [
            (RequestStatus.CREATED, float(tick))
        ]
        self.path: Optional[List["BaseNode"]] = []
        self.path_index = 0
        self.get_tick = get_tick
        self.tick_time = tick_time

        self.set_priority_type(self.priority)

    def debug_print(self, *args, **kwargs):
        """Print only if debug mode is enabled"""
        if self.debug:
            print(*args, **kwargs)

    def set_size(self, size: int | float):
        """Set request size"""
        self.size = size

    def set_priority_type(self, priority):
        """Set priority type"""
        match priority:
            case Priority.HIGH:
                self.qos_limit = 0.2  # 200 ms
                self.size = random.randint(1, 3) * 1e6  # bits
            case Priority.MEDIUM:
                self.qos_limit = 0.5  # 500 ms
                self.size = random.randint(4, 6) * 1e6  # bits
            case Priority.LOW:
                self.qos_limit = 1  # 1000 ms
                self.size = random.randint(7, 10) * 1e6  # bits
        self.debug_print(
            f"Request {self.id} created with size {self.size / 1000} kilo bytes"
        )

    def update_status(self, new_status: RequestStatus):
        """Update request status and track timing"""

        if (
            self.status == RequestStatus.COMPLETED
            or self.status == RequestStatus.FAILED
        ):
            return
        if (
            not ((self.get_tick() - self.creation_time) * self.tick_time)
            <= self.qos_limit
        ):
            self.status = RequestStatus.FAILED

        self.status_history.append((new_status, self.get_tick()))
        self.debug_print(
            f"Request {self.id} status changed: {self.status} -> {new_status} "
            f"(time in previous status: {self.get_tick() - self.last_status_change:.2f}s)"
        )
        self.status = new_status
        self.last_status_change = self.get_tick()

    def __str__(self):
        return (
            f"Priority: {self.priority} "
            f"Appearing time: {self.creation_time} "
            f"QoS limit: {self.qos_limit/self.tick_time} ticks "
            f"Target node: {self.target_node.name if self.target_node else 'None'} "
            f"Last status change: {self.last_status_change} "
            f"Status:{self.status}"
        )
