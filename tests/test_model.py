"""Unit tests for the Queue Paradox model."""
import numpy as np
import pytest

from model import (
    simulate,
    analyze,
    save_results,
    mm1_mean_wait,
    mmc_mean_wait,
    erlang_c,
    N_LANES,
    LAMBDA_TOTAL,
    MU,
)


def test_simulate_returns_valid_arrays():
    """The simulator must return three aligned non-negative arrays."""
    arr, srv, w = simulate("shortest", n_customers=500, seed=1)
    assert len(arr) == 500
    assert len(srv) == 500
    assert len(w) == 500
    assert np.all(w >= 0)


def test_waits_are_non_negative_for_all_strategies():
    """Queue waits cannot be negative under any policy."""
    for s in ("shortest", "random", "serpentine"):
        _, _, w = simulate(s, n_customers=400, seed=2)
        assert np.all(w >= 0), f"negative wait under {s!r}"


def test_serpentine_has_lower_mean_than_random():
    """Pooling servers should never be worse than random per-lane routing."""
    _, _, w_r = simulate("random", n_customers=4000, seed=3)
    _, _, w_s = simulate("serpentine", n_customers=4000, seed=3)
    assert np.mean(w_s) <= np.mean(w_r) + 0.05


def test_mm1_formula_matches_simulation_for_random():
    """Random routing makes each lane an M/M/1; theory should match sim."""
    _, _, w = simulate("random", n_customers=20_000, seed=4)
    lam_lane = LAMBDA_TOTAL / N_LANES
    theory = mm1_mean_wait(lam_lane, MU)
    sim = float(np.mean(w))
    # 30% tolerance: finite-sample noise + warm-up transient
    assert abs(sim - theory) / max(theory, 1e-9) < 0.30


def test_erlang_c_is_a_probability():
    """Erlang-C must lie in [0, 1] for stable systems."""
    for c in (1, 2, 5, 10):
        c_val = erlang_c(0.5, 0.4, c)
        assert 0.0 <= c_val <= 1.0


def test_mmc_wait_below_mm1_when_pooled():
    """Pooling c servers (M/M/c) should beat c separate M/M/1 lanes."""
    pooled = mmc_mean_wait(LAMBDA_TOTAL, MU, N_LANES)
    separate = mm1_mean_wait(LAMBDA_TOTAL / N_LANES, MU)
    assert pooled < separate


def test_reproducibility():
    """Same seed must produce identical wait arrays."""
    a = simulate("shortest", n_customers=300, seed=7)
    b = simulate("shortest", n_customers=300, seed=7)
    assert np.array_equal(a[2], b[2])


def test_analyze_returns_three_strategies():
    """analyze() must cover all three strategies in canonical order."""
    results = analyze(n_customers=500)
    assert [r.strategy for r in results] == \
        ["shortest", "random", "serpentine"]
    for r in results:
        assert r.mean_wait >= 0
        assert r.std_wait >= 0
        assert 0.0 <= r.p50_wait <= r.p95_wait <= r.p99_wait


def test_invalid_strategy_raises():
    """An unknown strategy string must raise ValueError."""
    with pytest.raises(ValueError):
        simulate("telepathic", n_customers=50)
