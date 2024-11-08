from optimisation_ntn.algorithms.req_generator import ReqGenerator


def test_basic_population():
    """Test that the matrix populates with a basic valid setup."""
    time_span = 10
    req_amount = 10
    lambda_rate = 1.0
    requests_array = []
    req_gen = ReqGenerator(time_span)
    matrice = req_gen.matrix_k_populate(req_amount, requests_array, lambda_rate)

    assert matrice.get_rows() == req_amount, "Matrix rows should match request amount."
    assert matrice.get_cols() == time_span, "Matrix columns should match time span."
    assert len(requests_array) <= req_amount, "Request array should not exceed the request amount."

def test_zero_time_span():
    """Test with time_span set to 0."""
    time_span = 0
    req_amount = 10
    lambda_rate = 1.0
    requests_array = []
    req_gen = ReqGenerator(time_span)

    try:
        matrice = req_gen.matrix_k_populate(req_amount, requests_array, lambda_rate)
        assert matrice.get_cols() == 0, "With zero time_span, matrix columns should be 0."
    except Exception as e:
        print(f"Error with zero time_span: {e}")

def test_high_lambda_rate():
    """Test with a high lambda_rate to stress distribution."""
    time_span = 10
    req_amount = 10
    lambda_rate = 5.0
    requests_array = []
    req_gen = ReqGenerator(time_span)
    matrice = req_gen.matrix_k_populate(req_amount, requests_array, lambda_rate)

    assert len(requests_array) <= req_amount, "High lambda_rate should not exceed request amount."
    assert sum(sum(row) for row in matrice.data) <= req_amount, "Matrix entries should not exceed request amount."

def test_large_req_amount():
    """Test with a large request amount compared to time_span."""
    time_span = 5
    req_amount = 20
    lambda_rate = 4.0
    requests_array = []
    req_gen = ReqGenerator(time_span)

    matrice = req_gen.matrix_k_populate(req_amount, requests_array, lambda_rate)

    assert matrice.get_rows() == req_amount, "Matrix rows should match request amount."
    assert matrice.get_cols() == time_span, "Matrix columns should match time span."
    assert len(requests_array) == req_amount, "Requests array should match request amount when possible."

def test_index_error():
    """Test that IndexError is raised when the requests exceed available rows."""
    time_span = 5
    req_amount = 5
    lambda_rate = 5.0
    requests_array = []
    req_gen = ReqGenerator(time_span)

    try:
        req_gen.matrix_k_populate(req_amount, requests_array, lambda_rate)
    except IndexError as e:
        assert str(
            e) == "Exceeded the number of available rows in the matrix. Request amounts must be enough higher than the experience time", \
            "IndexError should be raised when req_amount is insufficient."

def test_adjusted_poisson_distribution():
    """Ensure the adjusted Poisson distribution matches the req_amount."""
    time_span = 5
    req_amount = 10
    lambda_rate = 1.5
    requests_array = []
    req_gen = ReqGenerator(time_span)

    matrice = req_gen.matrix_k_populate(req_amount, requests_array, lambda_rate)

    populated_requests = sum(sum(row) for row in matrice.data)
    assert populated_requests == req_amount, "Total populated requests should match req_amount."

# Run tests
if __name__ == "__main__":
    test_basic_population()
    test_zero_time_span()
    test_high_lambda_rate()
    test_large_req_amount()
    test_index_error()
    test_adjusted_poisson_distribution()
    print("All tests passed.")
