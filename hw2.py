import numpy as np
import matplotlib.pyplot as plt

def fib(a, b):
    seq = [a, b]
    while len(seq) < 13:
        seq.append(seq[-2] + seq[-1])
    return seq

s1 = fib(0, 1)
s2 = fib(3, 7)

print("===== Problem 1: Fibonacci =====")
print()
print("Molecular Reactions (repeat 12 steps):")
print("  Phase 1 — copy A to temp:")
print("    A + Sf  --(kfast)-->  A + T        (A preserved, T = copy of A, Sf consumed)")
print("  Phase 2 — compute sum, shift:")
print("    A + Sf  --(kfast)-->  C + Sf")
print("    B + Sf  --(kfast)-->  C + Sf      (C = A + B)")
print("    T + Sf  --(kfast)-->  B + Sf      (T = old A becomes new B)")
print("  Phase 3 — update A:")
print("    C + Sf  --(kfast)-->  A + Sf      (sum C becomes new A)")
print()
print("Simulation (0, 1):")
for i, v in enumerate(s1):
    print(f"  F({i:2d}) = {v}")
print(f"  -> F(12) = {s1[12]}")
print()
print("Simulation (3, 7):")
for i, v in enumerate(s2):
    print(f"  F({i:2d}) = {v}")
print(f"  -> F(12) = {s2[12]}")

fig1, ax = plt.subplots(figsize=(9, 4))
ax.plot(range(13), s1, "b-o", label="start (0,1)")
ax.plot(range(13), s2, "r-s", label="start (3,7)")
for i, v in enumerate(s1):
    ax.annotate(str(v), (i, v), xytext=(0, 7), textcoords="offset points",
                fontsize=7, color="blue", ha="center")
for i, v in enumerate(s2):
    ax.annotate(str(v), (i, v), xytext=(0, -14), textcoords="offset points",
                fontsize=7, color="red", ha="center")
ax.set_xlabel("F(n) index")
ax.set_ylabel("Value")
ax.set_title("Problem 1: Fibonacci (12 steps)")
ax.legend()
plt.tight_layout()
plt.savefig("p1_fibonacci.png", dpi=150)
print()
print("Saved: p1_fibonacci.png")

print()
print("===== Problem 2: Biquad Filter =====")
print()
print("Filter equation:")
print("  Y[n] = (1/8)*X[n] + (1/8)*X[n-1] + (1/8)*X[n-2]")
print("       + (1/8)*Y[n-1] + (1/8)*Y[n-2]")
print()
print("Molecular Reactions:")
print()
print("Group 1 — fanout X to three paths (direct A, delay-1 C, delay-2 D):")
print("  g + X  --(kslow)-->  A + T        (X splits: A direct, T intermediate)")
print("  g + T  --(kslow)-->  C + D        (T splits: C for delay-1, D for delay-2)")
print()
print("Group 2 — direct term X[n] -> Y  (3 halvings = x1/8):")
print("  2A   --(kfast)-->  A2")
print("  2A2  --(kfast)-->  A4")
print("  2A4  --(kfast)-->  Y")
print()
print("Group 3 — delay-1 chain: C -> R1 -> G1 -> B1 -> F -> Y  (x1/8):")
print("  2C      --(kfast)-->  R1")
print("  b1 + R1 --(kslow)-->  G1")
print("  r1 + G1 --(kslow)-->  B1")
print("  g  + B1 --(kslow)-->  F")
print("  2F   --(kfast)-->  F2")
print("  2F2  --(kfast)-->  Y")
print()
print("Group 4 — delay-2 chain: D -> R2 -> G2 -> B2 -> E -> Y  (x1/8):")
print("  2D      --(kfast)-->  R2")
print("  b2 + R2 --(kslow)-->  G2")
print("  r2 + G2 --(kslow)-->  B2")
print("  g  + B2 --(kslow)-->  E")
print("  2E   --(kfast)-->  E2")
print("  2E2  --(kfast)-->  Y")
print()
print("Group 5 — fanout Y for two feedback paths (P = Y[n-1], Q = Y[n-2]):")
print("  b + Y  --(kslow)-->  P + Q        (blue-absence phase: after Y produced, before next X)")
print()
print("Group 6 — feedback delay-1: P -> R1f -> G1f -> B1f -> H -> Y  (x1/8):")
print("  2P       --(kfast)-->  R1f")
print("  b1 + R1f --(kslow)-->  G1f")
print("  r1 + G1f --(kslow)-->  B1f")
print("  g  + B1f --(kslow)-->  H")
print("  2H   --(kfast)-->  H2")
print("  2H2  --(kfast)-->  Y")
print()
print("Group 7 — feedback delay-2: Q -> R2f -> G2f -> B2f -> J -> Y  (x1/8):")
print("  2Q       --(kfast)-->  R2f")
print("  b2 + R2f --(kslow)-->  G2f")
print("  r2 + G2f --(kslow)-->  B2f")
print("  g  + B2f --(kslow)-->  J")
print("  2J   --(kfast)-->  J2")
print("  2J2  --(kfast)-->  Y")
print()
print("Group 8 — color concentration indicators (same structure as FIR example):")
print("  2R1  --(kfast)-->  2R1 + R1'    2G1  --(kfast)-->  2G1 + G1'")
print("  2B1  --(kfast)-->  2B1 + B1'    2R2  --(kfast)-->  2R2 + R2'")
print("  2G2  --(kfast)-->  2G2 + G2'    2B2  --(kfast)-->  2B2 + B2'")
print("  2R1' --(kfast)-->  null          2G1' --(kfast)-->  null  (etc.)")
print()
print("Group 9 — absence indicators (same structure as FIR example):")
print("  2Sr1 --(kslow)--> 2Sr1 + r1    R1' + r1 --(kfast)--> R1'  (etc.)")
print("  2Sg1 --(kslow)--> 2Sg1 + g1    G1' + g1 --(kfast)--> G1'  (etc.)")
print("  (repeat for b1, r2, g2, b2)")
print()

inputs = [100, 5, 500, 20, 250]
xh = [0, 0]
yh = [0, 0]
ys = []

for x in inputs:
    y = (x + xh[0] + xh[1] + yh[0] + yh[1]) / 8
    ys.append(y)
    xh = [x, xh[0]]
    yh = [y, yh[0]]

print("5-cycle simulation:")
print(f"  {'Cycle':<8} {'X input':<12} {'Y output'}")
print("  " + "-" * 32)
for i, (x, y) in enumerate(zip(inputs, ys)):
    print(f"  {i+1:<8} {x:<12} {y:.4f}")

fig2, axes = plt.subplots(2, 1, figsize=(8, 6))
axes[0].stem(range(1, 6), inputs, markerfmt="bo", linefmt="b-", basefmt="k-")
axes[0].set_title("Biquad Filter: Input X")
axes[0].set_ylabel("Concentration")
axes[0].set_xticks(range(1, 6))
axes[0].set_xticklabels([f"Cycle {i}" for i in range(1, 6)])

axes[1].stem(range(1, 6), ys, markerfmt="ro", linefmt="r-", basefmt="k-")
axes[1].set_title("Biquad Filter: Output Y")
axes[1].set_ylabel("Concentration")
axes[1].set_xlabel("Cycle")
axes[1].set_xticks(range(1, 6))
axes[1].set_xticklabels([f"Cycle {i}" for i in range(1, 6)])
for i, y in enumerate(ys):
    axes[1].annotate(f"{y:.2f}", (i+1, y), xytext=(0, 8), textcoords="offset points",
                     ha="center", fontsize=9)

plt.tight_layout()
plt.savefig("p2_biquad.png", dpi=150)
print()
print("Saved: p2_biquad.png")

plt.show()
