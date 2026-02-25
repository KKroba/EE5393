import random
import numpy as np

def props(x1, x2, x3):
    a1 = 0.5 * x1 * (x1 - 1) * x2
    a2 = x1 * x3 * (x3 - 1)
    a3 = 3 * x2 * x3
    return a1, a2, a3, a1 + a2 + a3

def step(x1, x2, x3):
    a1, a2, a3, total = props(x1, x2, x3)
    if total == 0:
        return x1, x2, x3
    r = random.random() * total
    if r < a1:
        return x1 - 2, x2 - 1, x3 + 4
    elif r < a1 + a2:
        return x1 - 1, x2 + 3, x3 - 2
    else:
        return x1 + 2, x2 - 1, x3 - 1

# ── Part (a) ──────────────────────────────────────────────────────────────────
# From S=[110,26,55], simulate until one of C1/C2/C3 is first reached.
# C1: x1>=150, C2: x2<10, C3: x3>100

N = 50000
c1, c2, c3 = 0, 0, 0
#ai help generated this logic
for _ in range(N):
    x1, x2, x3 = 110, 26, 55
    while True:
        if x1 >= 150: c1 += 1; break
        if x2 < 10:   c2 += 1; break
        if x3 > 100:  c3 += 1; break
        a1, a2, a3, total = props(x1, x2, x3)
        if total == 0: break
        x1, x2, x3 = step(x1, x2, x3)

print("Part (a) — from S=[110,26,55], first-passage probabilities:")
print(f"  Pr(C1) = {c1/N:.4f}   [x1 >= 150]")
print(f"  Pr(C2) = {c2/N:.4f}   [x2 < 10 ]")
print(f"  Pr(C3) = {c3/N:.4f}   [x3 > 100]")

# ── Part (b) ──────────────────────────────────────────────────────────────────
# From S=[9,8,7], after exactly 7 steps, compute mean and variance of X1,X2,X3.

M = 100000
X1, X2, X3 = [], [], []

for _ in range(M):
    x1, x2, x3 = 9, 8, 7
    for _ in range(7):
        a1, a2, a3, total = props(x1, x2, x3)
        if total == 0:
            break
        x1, x2, x3 = step(x1, x2, x3)
    X1.append(x1); X2.append(x2); X3.append(x3)

X1, X2, X3 = np.array(X1), np.array(X2), np.array(X3)

print("\nPart (b) — from S=[9,8,7], after 7 steps:")
for name, arr in [("X1", X1), ("X2", X2), ("X3", X3)]:
    print(f"  {name}: mean = {arr.mean():.4f},  variance = {arr.var():.4f}")