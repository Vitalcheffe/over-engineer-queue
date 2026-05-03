# Mathematical Derivation

## 1. Setup

We model `c = 10` checkout lanes. Customers arrive as a Poisson process
with total rate `lambda = 0.5` customers per minute and require
exponential service with rate `mu = 0.4` per minute per lane. The
per-lane utilization is

    rho_lane = (lambda / c) / mu = lambda / (c * mu)
             = 0.5 / (10 * 0.4) = 0.125

which is well below saturation. The pooled system is stable because
`lambda < c * mu`.

## 2. Three routing policies

1. **Pick shortest** — the arriving customer joins the lane with the
   fewest visible customers. This is "Join the Shortest Queue" (JSQ).
2. **Pick random** — the customer picks a lane uniformly at random.
3. **Serpentine** — a single FIFO queue feeds the first idle server.
   This is the classical M/M/c queue.

## 3. M/M/1 results (per-lane)

For "pick random" in steady state, each lane behaves as an independent
M/M/1 queue with arrival rate `lambda / c` and service rate `mu`. The
mean queue wait (excluding service) is

    E[W_q^{M/M/1}] = rho_lane / (mu - lambda / c)

and the variance is

    Var[W_q^{M/M/1}] = rho_lane / (mu - lambda / c)^2.

With our parameters this gives

    E[W_q^{M/M/1}] = 0.125 / (0.4 - 0.05) = 0.357 min ~= 21 s.

## 4. M/M/c results (serpentine)

For the serpentine queue, all `c` servers are pooled. The mean queue
wait is

    E[W_q^{M/M/c}] = C(c, lambda, mu) / (c * mu - lambda)

where `C(c, lambda, mu)` is the **Erlang-C probability** that an
arriving customer finds all `c` servers busy:

    C = (a^c / (c! (1 - rho))) /
        ( sum_{k=0}^{c-1} a^k / k! + a^c / (c! (1 - rho)) )

with `a = lambda / mu` (offered load per server) and
`rho = lambda / (c * mu)` (system utilization).

For our parameters, `a = 1.25` and `rho = 0.125`. Computing the
factorials and the geometric series gives `C ~= 8.4 x 10^-7`, so

    E[W_q^{M/M/c}] ~= 8.4e-7 / (4 - 0.5) ~= 2.4e-7 min.

In other words, the serpentine queue essentially never queues.

## 5. The paradox

Intuition says "pick shortest" should beat "pick random" because you
condition on joining a shorter queue. The catch is the symmetry of the
lanes: every arriving customer follows the same heuristic, so the
conditional distribution of the lane you join equals the marginal
distribution. By **PASTA** (Poisson Arrivals See Time Averages), the
snapshot you see is representative of the steady state.

What JSQ does shift is the variance: with shortest-line routing, the
queue lengths across lanes are anti-correlated, so the customer is
less likely to encounter a long queue. The expected wait may improve
under heavy load, but the variance reduction is the dominant effect
at the loads we simulate.

The serpentine queue collapses both: it is the unique policy that
fully pools the servers, and it is the policy every efficient airport
in the world uses.

## 6. Little's Law

For all three policies, Little's Law (Little, 1961) holds in steady
state:

    L = lambda * W

where `L` is the expected number of customers in system and `W` is the
expected sojourn time (queue wait + service). Pooling servers reduces
`L` without changing `lambda`, which is why the serpentine queue
dominates in expectation.

## 7. References

- Erlang, A. K. (1909). "Probability and Telephone Calls."
- Little, J. D. C. (1961). "A Proof for the Queuing Formula L = lambda W."
- Kingman, J. F. C. (1962). "On Queues in Heavy Traffic."
- Wolff, R. W. (1982). "Poisson Arrivals See Time Averages."
- Harchol-Balter, M. (2013). *Performance Modeling and Design of
  Computer Systems*. Cambridge University Press.
