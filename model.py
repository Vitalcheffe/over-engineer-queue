"""
The Queue Paradox — M/M/1 Queueing Theory + Discrete Event Simulation

At the supermarket, you pick the shortest line. The line next to you
goes faster. Why does this happen almost every time?

The setup: 10 checkout lanes, Poisson arrivals (lambda = 0.5/min total),
exponential service times (mu = 0.4/min per lane). We compare three
queueing strategies:

  1. "shortest"   -- join the lane with the fewest customers
  2. "random"     -- join a uniformly random lane
  3. "serpentine" -- single FIFO queue, dispatched to the first free
                     server (the M/M/c queue)

Little's Law (L = lambda * W) holds in all three. The paradox: picking
the shortest lane barely changes the expected wait relative to picking
randomly -- the symmetry of the lanes and PASTA wash out the perceived
gain. What changes is the variance. The serpentine queue collapses
both mean and variance, which is why every efficient airport in the
world uses one.
"""
import heapq
import json
import os
from dataclasses import dataclass, asdict, field
from typing import List, Tuple

import numpy as np

# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
N_LANES = 10
LAMBDA_TOTAL = 0.5          # arrivals per minute (Poisson process)
MU = 0.4                    # service rate per lane (exponential, per min)
N_CUSTOMERS = 10_000
SEED = 42


@dataclass
class StrategyResult:
    """Summary statistics for one routing strategy."""
    strategy: str
    n_lanes: int
    n_customers: int
    lambda_total: float
    mu: float
    rho_lane: float
    rho_system: float
    mean_wait: float
    std_wait: float
    p50_wait: float
    p95_wait: float
    p99_wait: float
    var_wait: float
    theoretical_mean_wait: float
    waits: List[float] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Discrete-event simulation
# ---------------------------------------------------------------------------
def simulate(strategy: str,
             n_lanes: int = N_LANES,
             n_customers: int = N_CUSTOMERS,
             lam: float = LAMBDA_TOTAL,
             mu: float = MU,
             seed: int = SEED) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Run a discrete-event simulation of `n_lanes` checkout lanes.

    Parameters
    ----------
    strategy : {"shortest", "random", "serpentine"}
        Routing policy for arriving customers.

    Returns
    -------
    arrivals, services, waits : np.ndarray
        Per-customer arrival times, service times, and queue waits
        (Wq = start_of_service - arrival; does not include service).
    """
    if strategy not in ("shortest", "random", "serpentine"):
        raise ValueError(f"unknown strategy: {strategy!r}")

    rng = np.random.default_rng(seed)

    # Poisson arrivals: exponential inter-arrival times
    inter = rng.exponential(1.0 / lam, size=n_customers)
    arrivals = np.cumsum(inter)
    # Exponential service times
    services = rng.exponential(1.0 / mu, size=n_customers)

    # Per-lane state
    next_free = [0.0] * n_lanes              # time the server becomes idle
    lane_queue: List[List[Tuple[int, float, float]]] = [[] for _ in range(n_lanes)]
    in_system = [0] * n_lanes                 # current number in lane

    # Event heap: (time, counter, kind, ...). The counter breaks ties so
    # that events with the same timestamp fire in insertion order.
    events: List[Tuple] = []
    counter = 0
    for i in range(n_customers):
        heapq.heappush(events, (float(arrivals[i]), counter, "arr", i))
        counter += 1

    waits = np.zeros(n_customers)

    while events:
        ev = heapq.heappop(events)
        t = ev[0]
        kind = ev[2]

        if kind == "arr":
            cid = ev[3]
            arr = float(arrivals[cid])
            srv = float(services[cid])

            if strategy == "serpentine":
                # Single FIFO queue, dispatched to the first idle server.
                lane = _pick_lane_serpentine(next_free)
                start = max(arr, next_free[lane])
                waits[cid] = start - arr
                next_free[lane] = start + srv
                heapq.heappush(events, (start + srv, counter, "dep", lane))
                counter += 1
            else:
                if strategy == "shortest":
                    lane = _pick_lane_shortest(in_system)
                else:  # random
                    lane = _pick_lane_random(rng, n_lanes)

                in_system[lane] += 1
                if next_free[lane] <= arr:
                    start = arr
                    next_free[lane] = start + srv
                    waits[cid] = 0.0
                    heapq.heappush(
                        events, (start + srv, counter, "dep_lane", lane))
                    counter += 1
                else:
                    lane_queue[lane].append((cid, srv, arr))

        elif kind == "dep_lane":
            lane = ev[3]
            in_system[lane] -= 1
            if lane_queue[lane]:
                cid, srv, arr = lane_queue[lane].pop(0)
                start = t
                waits[cid] = start - arr
                next_free[lane] = start + srv
                heapq.heappush(
                    events, (start + srv, counter, "dep_lane", lane))
                counter += 1
        # 'dep' (serpentine departure) needs no action -- next_free was
        # already updated when the customer was dispatched.

    return arrivals, services, waits


def _pick_lane_shortest(in_system: List[int]) -> int:
    """Join the lane with the fewest visible customers (ties: lowest idx)."""
    return int(np.argmin(in_system))


def _pick_lane_random(rng: np.random.Generator, n_lanes: int) -> int:
    """Join a uniformly random lane."""
    return int(rng.integers(0, n_lanes))


def _pick_lane_serpentine(next_free: List[float]) -> int:
    """Dispatch to the lane that becomes idle earliest."""
    return int(np.argmin(next_free))


# ---------------------------------------------------------------------------
# Theoretical queueing formulas
# ---------------------------------------------------------------------------
def mm1_mean_wait(lam: float, mu: float) -> float:
    """E[Wq] for an M/M/1 queue (queue wait, not including service)."""
    rho = lam / mu
    if rho >= 1.0:
        return float("inf")
    return rho / (mu - lam)


def erlang_c(lam: float, mu: float, c: int) -> float:
    """Probability an arriving customer to an M/M/c system has to wait."""
    a = lam / mu
    rho = lam / (c * mu)
    if rho >= 1.0:
        return 1.0
    s = 0.0
    term = 1.0
    for k in range(c):
        s += term
        term = term * a / (k + 1)
    last = term / (1.0 - rho)
    return last / (s + last)


def mmc_mean_wait(lam: float, mu: float, c: int) -> float:
    """E[Wq] for an M/M/c queue."""
    rho = lam / (c * mu)
    if rho >= 1.0:
        return float("inf")
    C = erlang_c(lam, mu, c)
    return C / (c * mu - lam)


# ---------------------------------------------------------------------------
# Analysis
# ---------------------------------------------------------------------------
def analyze(n_customers: int = N_CUSTOMERS,
            n_lanes: int = N_LANES,
            lam: float = LAMBDA_TOTAL,
            mu: float = MU,
            seed: int = SEED) -> List[StrategyResult]:
    """Run all three strategies and return summary statistics."""
    out: List[StrategyResult] = []
    rho_lane = lam / (n_lanes * mu)
    rho_system = lam / (n_lanes * mu)

    for strat in ("shortest", "random", "serpentine"):
        _, _, w = simulate(strat, n_lanes=n_lanes,
                           n_customers=n_customers,
                           lam=lam, mu=mu, seed=seed)
        if strat == "serpentine":
            theory = mmc_mean_wait(lam, mu, n_lanes)
        else:
            theory = mm1_mean_wait(lam / n_lanes, mu)
        out.append(StrategyResult(
            strategy=strat,
            n_lanes=n_lanes,
            n_customers=n_customers,
            lambda_total=lam,
            mu=mu,
            rho_lane=rho_lane,
            rho_system=rho_system,
            mean_wait=float(np.mean(w)),
            std_wait=float(np.std(w)),
            p50_wait=float(np.percentile(w, 50)),
            p95_wait=float(np.percentile(w, 95)),
            p99_wait=float(np.percentile(w, 99)),
            var_wait=float(np.var(w)),
            theoretical_mean_wait=float(theory),
            waits=[float(x) for x in w[:500]],
        ))
    return out


def save_results(path: str = "data/results.json") -> dict:
    """Run the analysis and persist results to JSON."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    results = analyze()
    payload = {
        "project": "over-engineer-queue",
        "date": "2026-07-12",
        "parameters": {
            "n_lanes": N_LANES,
            "n_customers": N_CUSTOMERS,
            "lambda_total_per_min": LAMBDA_TOTAL,
            "mu_per_min": MU,
            "lambda_per_lane_per_min": LAMBDA_TOTAL / N_LANES,
            "rho_lane": LAMBDA_TOTAL / (N_LANES * MU),
            "rho_system": LAMBDA_TOTAL / (N_LANES * MU),
            "seed": SEED,
        },
        "results": [asdict(r) for r in results],
        "summary": {
            "mean_wait_shortest_min": results[0].mean_wait,
            "mean_wait_random_min": results[1].mean_wait,
            "mean_wait_serpentine_min": results[2].mean_wait,
            "std_wait_shortest_min": results[0].std_wait,
            "std_wait_random_min": results[1].std_wait,
            "std_wait_serpentine_min": results[2].std_wait,
            "var_ratio_serpentine_to_random":
                results[2].var_wait / max(results[1].var_wait, 1e-12),
            "paradox_shortest_minus_random_min":
                results[0].mean_wait - results[1].mean_wait,
        },
    }
    with open(path, "w") as f:
        json.dump(payload, f, indent=2)
    return payload


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    payload = save_results()
    p = payload["parameters"]
    print(f"Simulation: {p['n_lanes']} lanes, "
          f"lambda={p['lambda_total_per_min']} /min, "
          f"mu={p['mu_per_min']} /min, "
          f"rho_lane={p['rho_lane']:.3f}")
    print()
    header = (f"{'Strategy':<12}{'E[Wq] min':>14}{'SD min':>10}"
              f"{'p50':>9}{'p95':>9}{'p99':>9}{'theory':>10}")
    print(header)
    print("-" * len(header))
    for r in payload["results"]:
        print(f"{r['strategy']:<12}{r['mean_wait']:>14.4f}"
              f"{r['std_wait']:>10.4f}{r['p50_wait']:>9.3f}"
              f"{r['p95_wait']:>9.3f}{r['p99_wait']:>9.3f}"
              f"{r['theoretical_mean_wait']:>10.4f}")
    s = payload["summary"]
    print()
    print(f"Paradox (shortest - random): "
          f"{s['paradox_shortest_minus_random_min']:+.4f} min")
    print(f"Variance ratio (serpentine / random): "
          f"{s['var_ratio_serpentine_to_random']:.4f}")
