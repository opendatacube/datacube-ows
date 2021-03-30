from datacube_ows.query_profiler import QueryProfiler


def test_qpf_inactive():
    qp = QueryProfiler(False)
    qp.start_event("foo")
    qp.end_event("foo")
    qp["foo"] = "splunge"
    assert qp.profile() == {}


def test_qpf_active():
    qp = QueryProfiler(True)
    prof = qp.profile()
    assert prof["info"] == {}
    assert prof["profile"]["query"] is not None


def test_qpf_events():
    qp = QueryProfiler(True)
    qp.start_event("foo")
    qp.end_event("foo")
    prof = qp.profile()
    assert prof["profile"]["foo"] is not None


def test_qpf_info():
    qp = QueryProfiler(True)
    qp["foo"] = "splunge"
    prof = qp.profile()
    assert prof["info"]["foo"] == "splunge"

