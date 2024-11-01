import numpy as np
import random

from optimisation_ntn.matrices.base_matrice import Matrice
from optimisation_ntn.users.request import Request

class ReqGenerator:
    def __init__(self, time_span: int, req_amount: int):
        self.time_span = time_span
        self.req_amount = req_amount

    def generate(self):
        matrice = Matrice(self.time_span, self.time_span)  # Initialize the matrix

        lambda_rate = self.req_amount / self.time_span

        for tick in range(self.time_span):
            request_count = np.random.poisson(lambda_rate)

            for _ in range(request_count):
                request_id = random.randint(1, 3)
                matrice.set_element(tick, random.randint(0, self.time_span - 1), Request(request_id, tick).id)

        return matrice
