from decimal import Decimal

from hypothesis import given, strategies as st

from backend.app.services.session_service import calculate_session_cost

money = st.decimals(min_value=0, max_value=500, places=2)


@given(energy=money, increment=money, rate=money, fee=money, tax=st.decimals(min_value=0, max_value=100, places=2))
def test_adding_energy_cannot_reduce_price(energy, increment, rate, fee, tax):
    def cost(kwh):
        return calculate_session_cost(kwh, rate, Decimal("1.125"), fee, tax)

    assert cost(Decimal(0)) >= fee
    assert cost(energy + increment) >= cost(energy)
