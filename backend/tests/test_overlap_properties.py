from datetime import datetime, timedelta, timezone

from hypothesis import HealthCheck, given, settings, strategies as st
from sqlalchemy import text


@settings(max_examples=40, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(
    a_start=st.integers(min_value=0, max_value=30),
    a_length=st.integers(min_value=1, max_value=20),
    b_start=st.integers(min_value=0, max_value=30),
    b_length=st.integers(min_value=1, max_value=20),
)
def test_postgres_half_open_overlap_matches_the_intersection_of_minutes(
    db_session, a_start, a_length, b_start, b_length,
):
    origin = datetime(2026, 1, 1, tzinfo=timezone.utc)
    bounds = {
        "a1": origin + timedelta(minutes=a_start),
        "a2": origin + timedelta(minutes=a_start+a_length),
        "b1": origin + timedelta(minutes=b_start),
        "b2": origin + timedelta(minutes=b_start+b_length),
    }
    database_overlap = db_session.scalar(text(
        "SELECT tstzrange(:a1, :a2, '[)') && tstzrange(:b1, :b2, '[)')"
    ), bounds)
    expected = bool(set(range(a_start, a_start + a_length)) & set(range(b_start, b_start + b_length)))
    assert database_overlap == expected
