# M/M/1 Notes

## The M/M/1 queue

A single-server queue with:
- **M**emoryless (Poisson) arrivals, rate `lambda`
- **M**emoryless (exponential) service, rate `mu`
- 1 server, infinite queue capacity, FCFS

## Stability

The system is stable iff `rho = lambda / mu < 1`. Above 1 the queue
grows without bound.

## Steady-state distribution

The number of customers in the system is geometric:

    P(N = k) = (1 - rho) * rho^k

with mean `E[N] = rho / (1 - rho)`.

## Wait times

The queue wait (excluding service) has an atom at zero and an
exponential tail:

    P(W_q > t) = rho * exp(-(mu - lambda) * t)
    P(W_q = 0) = 1 - rho

Mean and variance:

    E[W_q] = rho / (mu - lambda)
    Var[W_q] = rho / (mu - lambda)^2

The sojourn (total time in system) is exponential:

    W = W_q + S,    E[W] = 1 / (mu - lambda),    Var[W] = 1 / (mu - lambda)^2

## Little's Law

    L = lambda * W

Holds for any stable queue in steady state.

## Application to multi-lane

With `c` independent M/M/1 lanes and uniform random routing, each lane
sees arrival rate `lambda / c`. The per-lane load is

    rho_lane = lambda / (c * mu).

Total expected number in system:

    E[L_total] = c * rho_lane / (1 - rho_lane)
               = lambda / (mu - lambda / c).

This is **worse** than a single M/M/c queue with the same total load
because pooling reduces `rho` and the idle servers can pick up work
from any arrival.
