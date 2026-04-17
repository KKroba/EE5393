

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Dict, List, Sequence, Tuple
import collections
import math
import random



def F(x) -> Fraction:
    if isinstance(x, Fraction):
        return x
    return Fraction(x)


def frac_str(x: Fraction) -> str:
    return f"{x.numerator}/{x.denominator}" if x.denominator != 1 else str(x.numerator)


def fmt_prob(x: Fraction | float, digits: int = 10) -> str:
    if isinstance(x, Fraction):
        return f"{float(x):.{digits}f}"
    return f"{x:.{digits}f}"



def power_to_bernstein(power_coeffs: Sequence[Fraction]) -> List[Fraction]:
    n = len(power_coeffs) - 1
    out: List[Fraction] = []
    for k in range(n + 1):
        s = Fraction(0, 1)
        for i in range(k + 1):
            s += power_coeffs[i] * Fraction(math.comb(k, i), math.comb(n, i))
        out.append(s)
    return out


def bernstein_eval(coeffs: Sequence[Fraction], x: float) -> float:
    n = len(coeffs) - 1
    total = 0.0
    for k, bk in enumerate(coeffs):
        total += float(bk) * math.comb(n, k) * (x ** k) * ((1 - x) ** (n - k))
    return total


def bernstein_eval_fraction(coeffs: Sequence[Fraction], x: Fraction) -> Fraction:
    n = len(coeffs) - 1
    total = Fraction(0, 1)
    for k, bk in enumerate(coeffs):
        total += bk * Fraction(math.comb(n, k), 1) * (x ** k) * ((1 - x) ** (n - k))
    return total


def bernstein_approximation_of_function(func, degree: int) -> List[Fraction]:
    coeffs = []
    for k in range(degree + 1):
        x = k / degree if degree > 0 else 0.0
        coeffs.append(Fraction(func(x)).limit_denominator(10**6))
    return coeffs


def generalized_mux_description(var_name: str, bern_coeffs: Sequence[Fraction]) -> str:
    n = len(bern_coeffs) - 1
    lines = []
    lines.append(f"Degree n = {n}")
    lines.append(
        f"Use {n} independent stochastic inputs {var_name}_1, ..., {var_name}_{n}, each with probability {var_name}."
    )
    lines.append(f"Count the number K of ones among those {n} inputs.")
    lines.append("Generalized MUX selects constant input b_K where:")
    for k, bk in enumerate(bern_coeffs):
        lines.append(f"  b_{k} = {frac_str(bk)}   (~ {fmt_prob(bk, 8)})")
    lines.append(
        f"Then output probability is sum_k b_k * C({n},k) * {var_name}^k * (1-{var_name})^({n}-k)."
    )
    return "\n".join(lines)


def simulate_generalized_mux(
    x: float,
    bern_coeffs: Sequence[Fraction],
    n_bits: int = 100_000,
    rng_seed: int = 0,
) -> float:
    rng = random.Random(rng_seed)
    n = len(bern_coeffs) - 1
    ones = 0
    for _ in range(n_bits):
        k = 0
        for _ in range(n):
            if rng.random() < x:
                k += 1
        if rng.random() < float(bern_coeffs[k]):
            ones += 1
    return ones / n_bits



class Expr:
    def prob(self) -> Fraction:
        raise NotImplementedError

    def pretty(self) -> str:
        raise NotImplementedError

    def to_and_not(self) -> str:
        raise NotImplementedError


@dataclass(frozen=True)
class Const(Expr):
    value: int

    def prob(self) -> Fraction:
        return Fraction(self.value, 1)

    def pretty(self) -> str:
        return str(self.value)

    def to_and_not(self) -> str:
        return str(self.value)


@dataclass(frozen=True)
class SourceExpr(Expr):
    name: str
    p: Fraction

    def prob(self) -> Fraction:
        return self.p

    def pretty(self) -> str:
        return self.name

    def to_and_not(self) -> str:
        return self.name


@dataclass(frozen=True)
class NotExpr(Expr):
    child: Expr

    def prob(self) -> Fraction:
        return 1 - self.child.prob()

    def pretty(self) -> str:
        return f"~({self.child.pretty()})"

    def to_and_not(self) -> str:
        return f"~({self.child.to_and_not()})"


@dataclass(frozen=True)
class AndExpr(Expr):
    left: Expr
    right: Expr

    def prob(self) -> Fraction:
        return self.left.prob() * self.right.prob()

    def pretty(self) -> str:
        return f"({self.left.pretty()} & {self.right.pretty()})"

    def to_and_not(self) -> str:
        return f"({self.left.to_and_not()} & {self.right.to_and_not()})"


@dataclass(frozen=True)
class OrExpr(Expr):
    left: Expr
    right: Expr

    def prob(self) -> Fraction:
        a, b = self.left.prob(), self.right.prob()
        return a + b - a * b

    def pretty(self) -> str:
        return f"({self.left.pretty()} | {self.right.pretty()})"

    def to_and_not(self) -> str:
        return f"~((~({self.left.to_and_not()})) & (~({self.right.to_and_not()})))"


P40 = SourceExpr("p40", Fraction(2, 5))
P50 = SourceExpr("p50", Fraction(1, 2))
ZERO = Const(0)
ONE = Const(1)


def apply_move(expr: Expr, move: Tuple[str, Fraction] | Tuple[str]) -> Expr:
    kind = move[0]
    if kind == "NOT":
        return NotExpr(expr)

    s = move[1]
    source = P40 if s == Fraction(2, 5) else P50

    if kind == "MUL_S":
        return AndExpr(source, expr)
    if kind == "MUL_1-S":
        return AndExpr(NotExpr(source), expr)
    if kind == "AFF_S":
        return OrExpr(source, expr)
    if kind == "AFF_1-S":
        return OrExpr(NotExpr(source), expr)

    raise ValueError(f"Unknown move: {move}")


def synthesize_probability(
    target: Fraction,
    sources: Sequence[Fraction] = (Fraction(2, 5), Fraction(1, 2)),
    max_depth: int = 80,
) -> Expr:
    base_map: Dict[Fraction, Expr] = {
        Fraction(0, 1): ZERO,
        Fraction(1, 1): ONE,
        Fraction(2, 5): P40,
        Fraction(1, 2): P50,
        Fraction(3, 5): NotExpr(P40),
    }

    dq = collections.deque([target])
    dist: Dict[Fraction, int] = {target: 0}
    parent: Dict[Fraction, Fraction] = {}
    move: Dict[Fraction, Tuple[str, Fraction] | Tuple[str]] = {}

    while dq:
        v = dq.popleft()
        if v in base_map:
            expr = base_map[v]
            cur = v
            while cur != target:
                expr = apply_move(expr, move[cur])
                cur = parent[cur]
            if expr.prob() != target:
                raise RuntimeError("Synthesis bug: probability mismatch.")
            return expr

        d = dist[v]
        if d >= max_depth:
            continue

        cands: List[Tuple[Fraction, Tuple[str, Fraction] | Tuple[str]]] = []
        cands.append((1 - v, ("NOT",)))

        for s in sources:
            one_minus_s = 1 - s

            q = v / s
            if 0 <= q <= 1:
                cands.append((q, ("MUL_S", s)))

            q = v / one_minus_s
            if 0 <= q <= 1:
                cands.append((q, ("MUL_1-S", s)))

            q = (v - s) / one_minus_s
            if 0 <= q <= 1:
                cands.append((q, ("AFF_S", s)))

            q = (v - one_minus_s) / s
            if 0 <= q <= 1:
                cands.append((q, ("AFF_1-S", s)))

        for nv, act in cands:
            if nv not in dist:
                dist[nv] = d + 1
                parent[nv] = v
                move[nv] = act
                dq.append(nv)

    raise ValueError(f"Failed to synthesize target {target}")



def problem_1a_data():
    power = [Fraction(0), Fraction(1), Fraction(-1, 4)]
    bern = power_to_bernstein(power)
    return power, bern


def problem_1b_data(degree: int = 8):
    bern = bernstein_approximation_of_function(math.cos, degree)
    return bern


def problem_1c_data():
    power = [
        Fraction(1, 2),
        Fraction(-5, 4),
        Fraction(5, 4),
        Fraction(-5, 8),
        Fraction(5, 32),
        Fraction(31, 32),
    ]
    bern = power_to_bernstein(power)
    demo_x = [
        Fraction(0, 1),
        Fraction(1, 4),
        Fraction(1, 2),
        Fraction(3, 4),
        Fraction(1, 1),
    ]
    demo_y = [bernstein_eval_fraction(bern, x) for x in demo_x]
    return power, bern, demo_x, demo_y


def problem_2a_targets():
    return [
        Fraction("0.8881188"),
        Fraction("0.2119209"),
        Fraction("0.5555555"),
    ]


def problem_2b_targets():
    return [
        Fraction(int("1011111", 2), 2**7),
        Fraction(int("1101111", 2), 2**7),
        Fraction(int("1010111", 2), 2**7),
    ]



def build_report() -> str:
    lines: List[str] = []

    lines.append("=" * 78)
    lines.append("EE 5393 HW1 solver / implementation report")
    lines.append("=" * 78)

    lines.append("\n[Problem 1(a)]  f(x) = x - x^2/4")
    power, bern = problem_1a_data()
    lines.append("Power-basis coefficients a_i:")
    lines.append("  " + ", ".join(frac_str(a) for a in power))
    lines.append("Exact Bernstein coefficients b_k:")
    lines.append("  " + ", ".join(frac_str(b) for b in bern))
    lines.append(generalized_mux_description("x", bern))

    lines.append("\n[Problem 1(b)]  Approximate cos(x) on [0,1]")
    degree = 8
    bern_cos = problem_1b_data(degree=degree)
    lines.append(f"Using degree-{degree} Bernstein approximation to cos(x) on [0,1].")
    lines.append("Bernstein coefficients b_k = cos(k/n):")
    lines.append("  " + ", ".join(frac_str(b) for b in bern_cos))
    lines.append(generalized_mux_description("x", bern_cos))
    for x in [0.0, 0.25, 0.5, 0.75, 1.0]:
        approx = bernstein_eval(bern_cos, x)
        exact = math.cos(x)
        lines.append(
            f"  x={x:>4.2f}: approx={approx:.10f}, exact cos(x)={exact:.10f}, abs err={abs(approx-exact):.10e}"
        )

    lines.append("\n[Problem 1(c)]")
    power_c, bern_c, demo_x, demo_y = problem_1c_data()
    lines.append("Power-basis coefficients a_i:")
    lines.append("  " + ", ".join(frac_str(a) for a in power_c))
    lines.append("Exact Bernstein coefficients b_k:")
    lines.append("  " + ", ".join(frac_str(b) for b in bern_c))
    lines.append(generalized_mux_description("t", bern_c))
    lines.append("Demonstration at requested X values:")
    for x, y in zip(demo_x, demo_y):
        lines.append(
            f"  X = {frac_str(x):>4s} -> output = {frac_str(y):>12s}  (~ {fmt_prob(y, 10)})"
        )

    lines.append("\n[Problem 2(a)]  Source probabilities {0.4, 0.5}")
    for target in problem_2a_targets():
        expr = synthesize_probability(target, sources=(Fraction(2, 5), Fraction(1, 2)))
        lines.append(f"Target {fmt_prob(target, 7)} = {frac_str(target)}")
        lines.append(f"  readable:   {expr.pretty()}")
        lines.append(f"  AND/NOT:    {expr.to_and_not()}")
        lines.append(f"  verified p: {frac_str(expr.prob())}")

    lines.append("\n[Problem 2(b)]  Source probabilities {0.5}")
    for target in problem_2b_targets():
        expr = synthesize_probability(target, sources=(Fraction(1, 2),))
        lines.append(f"Target {fmt_prob(target, 7)} = {frac_str(target)}")
        lines.append(f"  readable:   {expr.pretty()}")
        lines.append(f"  AND/NOT:    {expr.to_and_not()}")
        lines.append(f"  verified p: {frac_str(expr.prob())}")

    return "\n".join(lines)


def main():
    report = build_report()
    print(report)


if __name__ == "__main__":
    main()
