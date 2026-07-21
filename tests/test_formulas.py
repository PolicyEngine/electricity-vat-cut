"""Unit tests for the pure-Python VAT arithmetic (no PolicyEngine needed)."""

import numpy as np
import pytest

from electricity_vat_cut.formulas import vat_component, window_gain


def test_vat_component_of_105_is_5():
    # £105 of VAT-inclusive spending contains exactly £5 of VAT at 5%.
    assert np.isclose(vat_component(105.0), 5.0)


def test_vat_component_zero_spending():
    assert vat_component(0.0) == 0.0


def test_vat_component_array():
    gains = vat_component(np.array([0.0, 105.0, 1050.0]))
    assert np.allclose(gains, [0.0, 5.0, 50.0])


def test_vat_component_negative_spending_raises():
    with pytest.raises(ValueError, match="non-negative"):
        vat_component(np.array([100.0, -1.0]))


def test_vat_component_partial_cut():
    # 5% -> 2.5%: half the VAT component.
    assert np.isclose(vat_component(105.0, 0.05, 0.025), 2.5)


def test_vat_component_rate_increase_raises():
    with pytest.raises(ValueError, match="cut"):
        vat_component(105.0, 0.05, 0.20)


def test_vat_component_negative_rate_raises():
    with pytest.raises(ValueError, match="non-negative"):
        vat_component(105.0, -0.05, 0.0)


def test_window_gain_uniform_half_year():
    assert window_gain(100.0, 0.5) == 50.0


def test_window_gain_winter_weighted():
    assert np.isclose(window_gain(100.0, 0.575), 57.5)


def test_window_gain_out_of_range_raises():
    with pytest.raises(ValueError, match="window_share"):
        window_gain(100.0, 1.5)


def test_formulas_preserve_pandas_series():
    # Arithmetic must dispatch through pandas so MicroSeries weights
    # survive; a plain Series stands in for MicroSeries here.
    import pandas as pd

    spending = pd.Series([105.0, 210.0])
    gain = vat_component(spending)
    assert isinstance(gain, pd.Series)
    assert isinstance(window_gain(gain, 0.5), pd.Series)
