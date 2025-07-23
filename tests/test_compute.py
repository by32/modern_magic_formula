from etl.compute import compute_earnings_yield

def test_ey():
    assert compute_earnings_yield(100, 1000) == 0.1
