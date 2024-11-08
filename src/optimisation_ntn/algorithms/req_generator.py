import numpy as np
import random

from optimisation_ntn.matrices.base_matrice import Matrice
from optimisation_ntn.networks.request import Request

class ReqGenerator:
    def __init__(self, time_span: int):
        self.time_span = time_span

    def matrix_k_populate(self, req_amount: int, requests_array, lambda_rate: float):
        """This function will generate requests and populate a matrix with rows as requests and columns as time ticks."""
        matrice = Matrice(req_amount, self.time_span)
        matrice.zeros_matrix()

        poisson_array = np.random.poisson(lambda_rate, self.time_span)
        total_requests = poisson_array.sum()
        difference = req_amount - total_requests

        if difference != 0:
            if difference > 0:
                for _ in range(difference):
                    random_tick = random.choice(range(self.time_span))
                    poisson_array[random_tick] += 1
            elif difference < 0:
                for _ in range(-difference):
                    random_tick = random.choice(range(self.time_span))
                    if poisson_array[random_tick] > 0:
                        poisson_array[random_tick] -= 1

        current_row = 0
        for tick in range(self.time_span):
            request_count = poisson_array[tick]

            for req in range(request_count):
                """
                We lose some request at the end of the experience due to the random distribution of the requests on each 
                tick. The last tick might receive more requests, which makes the total amount of request greater than 
                the one we established.
                """
                if current_row >= req_amount:
                    break

                new_req = Request(tick)
                new_req.set_id(req, tick)

                requests_array.append(new_req)

                matrice.set_element(current_row, tick, 1)

                current_row += 1

            if current_row >= req_amount:
                break

        return matrice