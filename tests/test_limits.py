from agent import limits


def test_per_ip_limit():
    limits.reset()
    for _ in range(limits.PER_IP_HOUR):
        assert limits.allow("1.2.3.4", now=1000) == "ok"
    assert limits.allow("1.2.3.4", now=1000) == "ip"
    assert limits.allow("5.6.7.8", now=1000) == "ok"
    assert limits.allow("1.2.3.4", now=1000 + 3601) == "ok"
