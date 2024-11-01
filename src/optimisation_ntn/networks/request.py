class Request:
    def __init__(self, request_id: int, priority: int, data_size: int):
        self.request_id = request_id
        self.priority = priority
        self.data_size = data_size

    def __str__(self):
        return f"Request {self.request_id} with priority {self.priority}"
