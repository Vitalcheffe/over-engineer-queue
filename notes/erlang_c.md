# Erlang-C Formula

## Setup

A queue with `c` identical servers, Poisson arrivals (rate `lambda`),
exponential service (rate `mu`), infinite queue capacity, FCFS
discipline. This is the **M/M/c** queue.

## Utilization

    rho = lambda / (c * mu)

The system is stable iff `rho < 1`.

## Erlang-C: probability of queueing

The Erlang-C formula gives the probability an arriving customer finds
all `c` servers busy (and therefore must wait):

    C(c, lambda, mu) = [ a^c / (c! (1 - rho)) ]
                       / [ sum_{k=0}^{c-1} a^k / k!
                           + a^c / (c! (1 - rho)) ]

where `a = lambda / mu` is the offered load per server (note: this is
*not* the utilization).

## Mean queue wait

    E[W_q] = C(c, lambda, mu) / (c * mu - lambda)

The mean sojourn (queue + service):

    E[W] = E[W_q] + 1 / mu

## Numerical example

For `c = 10`, `lambda = 0.5`, `mu = 0.4`:

    a = 1.25
    rho = 0.125
    a^10 / 10! = 1.25^10 / 3628800 = 9.313 / 3628800 ~= 2.57e-6
    (1 - rho) = 0.875
    a^c / (c! (1 - rho)) ~= 2.93e-6
    sum_{k=0}^{9} a^k / k! ~= 3.49
    C = 2.93e-6 / (3.49 + 2.93e-6) ~= 8.4e-7
    E[W_q] = 8.4e-7 / (4 - 0.5) ~= 2.4e-7 min

This is essentially zero: with 10 pooled servers and a 12.5% load,
queueing almost never happens.

## Why pooling wins

The difference between `c` separate M/M/1 lanes (random routing) and
one M/M/c queue (serpentine) is the difference between `rho_lane` and
`rho_system`. When `rho_lane` is small, the per-lane M/M/1 mean wait
is approximately `rho_lane / mu`, which is much larger than the M/M/c
mean wait (which scales with Erlang-C, exponentially small in `c`).

Pooling converts an exponential penalty into an exponentially small one.

## Computation

Computing `C(c, lambda, mu)` directly via factorials is numerically
unstable for large `c`. The standard trick is to compute the recursion

    r_0 = 1
    r_k = r_{k-1} * a / k

so that `r_k = a^k / k!` without overflow. We use this recursion in
`erlang_c()` in `model.py`.

## References

- Erlang, A. K. (1917). "Solution of Some Problems in the Theory of
  Probabilities of Significance in Automatic Telephone Exchanges."
- Harchol-Balter (2013), ch. 14.
- Wolff (1989). *Stochastic Modeling and the Theory of Queues*.
