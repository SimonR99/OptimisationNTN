import random
import uuid
import time

class Request:

    lamda = 0
    size = 0
    cycle_bits = 0
    id = 0

    def __init__(self, priority: int, tick: int):
        self.priority = priority
        self.tick = tick #A quelle tick cette requête est apparu
        self.satisfaction = False
        self.set_priority_type()

    def set_priority_type (self):
        match self.priority:
            case 1:
                self.lamda = 0.2
                self.size = random.randint(1, 3)
                self.cycle_bits = random.randint(100,  130)
            case 2:
                self.lamda = 0.5
                self.size = random.randint(4, 6)
                self.cycle_bits = random.randint(131,  160)
            case 3:
                self.lamda = 1
                self.size = random.randint(7, 10)
                self.cycle_bits = random.randint(161,  200)

    def set_satisfied(self):
        self.satisfaction = True

    def set_unsatisfied(self):
        self.satisfaction = False



