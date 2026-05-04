from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.pdfgen.canvas import Canvas


Perm = tuple[int, int, int, int, int]
ID: Perm = (1, 2, 3, 4, 5)
SOURCE_LINK = "https://github.com/KKroba/EE5393/blob/main/hw4.py"


def cycle_perm(entries: list[int]) -> Perm:
    mapping = list(range(6))
    for a, b in zip(entries, entries[1:] + entries[:1]):
        mapping[a] = b
    return tuple(mapping[1:])


def compose(left: Perm, right: Perm) -> Perm:
    return tuple(right[i - 1] for i in left)


def inverse(perm: Perm) -> Perm:
    inv = [0] * len(perm)
    for i, j in enumerate(perm, start=1):
        inv[j - 1] = i
    return tuple(inv)


def perm_product(perms: list[Perm]) -> Perm:
    result = ID
    for perm in perms:
        result = compose(result, perm)
    return result


BASE_PERMS: dict[str, Perm] = {
    "A": cycle_perm([1, 4, 3, 5, 2]),
    "B": cycle_perm([1, 4, 5, 2, 3]),
    "C": cycle_perm([1, 3, 4, 2, 5]),
    "D": cycle_perm([1, 2, 4, 5, 3]),
    "E": cycle_perm([1, 4, 2, 3, 5]),
}

BASE_CYCLES: dict[str, str] = {
    "A": "(1 4 3 5 2)",
    "B": "(1 4 5 2 3)",
    "C": "(1 3 4 2 5)",
    "D": "(1 2 4 5 3)",
    "E": "(1 4 2 3 5)",
}


@dataclass(frozen=True)
class Sym:
    name: str
    inv: bool = False

    def inverse(self) -> "Sym":
        return Sym(self.name, not self.inv)

    def __str__(self) -> str:
        return f"{self.name}'" if self.inv else self.name


Atom = tuple[Sym, ...]
STAR: Atom = ()


def atom_text(atom: Atom) -> str:
    return "*" if not atom else "".join(str(sym) for sym in atom)


def atom_perm(atom: Atom) -> Perm:
    return perm_product([sym_perm(sym) for sym in atom])


def sym_perm(sym: Sym) -> Perm:
    base = BASE_PERMS[sym.name]
    return inverse(base) if sym.inv else base


def word(*symbols: Sym) -> Atom:
    return simplify_word(symbols)


def simplify_word(symbols: tuple[Sym, ...]) -> Atom:
    stack: list[Sym] = []
    for sym in symbols:
        if stack and stack[-1].name == sym.name and stack[-1].inv != sym.inv:
            stack.pop()
        else:
            stack.append(sym)
    return tuple(stack)


def append_word(prefix: Atom, suffix: Atom) -> Atom:
    return simplify_word(prefix + suffix)


A = Sym("A")
B = Sym("B")
C = Sym("C")
D = Sym("D")
E = Sym("E")


COMMUTATORS: dict[Sym, list[Sym]] = {
    A: [C, B, C.inverse(), B.inverse()],
    A.inverse(): [B, C, B.inverse(), C.inverse()],
    B: [C, D, C.inverse(), D.inverse()],
    B.inverse(): [D, C, D.inverse(), C.inverse()],
    C: [D, E, D.inverse(), E.inverse()],
    C.inverse(): [E, D, E.inverse(), D.inverse()],
    D: [E, B, E.inverse(), B.inverse()],
    D.inverse(): [B, E, B.inverse(), E.inverse()],
    E: [D, A, D.inverse(), A.inverse()],
    E.inverse(): [A, D, A.inverse(), D.inverse()],
}


@dataclass(frozen=True)
class VarExpr:
    name: str


@dataclass(frozen=True)
class NotExpr:
    child: "BoolExpr"


@dataclass(frozen=True)
class AndExpr:
    left: "BoolExpr"
    right: "BoolExpr"


@dataclass(frozen=True)
class OrExpr:
    left: "BoolExpr"
    right: "BoolExpr"


BoolExpr = VarExpr | NotExpr | AndExpr | OrExpr


def expr_text(expr: BoolExpr) -> str:
    if isinstance(expr, VarExpr):
        return expr.name
    if isinstance(expr, NotExpr):
        return f"({expr_text(expr.child)})'"
    if isinstance(expr, AndExpr):
        return f"{wrap_text(expr.left)}{wrap_text(expr.right)}"
    if isinstance(expr, OrExpr):
        return f"{wrap_text(expr.left)} + {wrap_text(expr.right)}"
    raise TypeError(expr)


def wrap_text(expr: BoolExpr) -> str:
    text = expr_text(expr)
    if isinstance(expr, (OrExpr, NotExpr)):
        return f"({text})"
    return text


def eval_bool(expr: BoolExpr, values: dict[str, int]) -> int:
    if isinstance(expr, VarExpr):
        return int(values[expr.name])
    if isinstance(expr, NotExpr):
        return 1 - eval_bool(expr.child, values)
    if isinstance(expr, AndExpr):
        return int(eval_bool(expr.left, values) and eval_bool(expr.right, values))
    if isinstance(expr, OrExpr):
        return int(eval_bool(expr.left, values) or eval_bool(expr.right, values))
    raise TypeError(expr)


@dataclass(frozen=True)
class Line:
    condition: str
    when_one: Atom
    when_zero: Atom

    def text(self) -> str:
        return f"{{{self.condition}: {atom_text(self.when_one)}, {atom_text(self.when_zero)}}}"

    def evaluate(self, values: dict[str, int]) -> Perm:
        if self.condition == "*":
            return atom_perm(self.when_one)
        return atom_perm(self.when_one if values[self.condition] else self.when_zero)


class LinkCanvas(Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pages = []

    def showPage(self):
        self.pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self.pages)
        for i, page in enumerate(self.pages, start=1):
            self.__dict__.update(page)
            if i == page_count:
                self.setFont("Helvetica", 8)
                self.setFillColor(colors.HexColor("#444444"))
                self.drawCentredString(letter[0] / 2, 0.32 * inch, SOURCE_LINK)
                self.linkURL(
                    SOURCE_LINK,
                    (0.55 * inch, 0.22 * inch, letter[0] - 0.55 * inch, 0.45 * inch),
                    relative=0,
                )
            super().showPage()
        super().save()


def expand(expr: BoolExpr, target: Sym) -> list[Line]:
    if isinstance(expr, VarExpr):
        return [Line(expr.name, word(target), STAR)]

    if isinstance(expr, NotExpr):
        child = expr.child
        if isinstance(child, VarExpr):
            return [Line(child.name, STAR, word(target))]
        lines = expand(child, target.inverse())
        return absorb_unconditional(lines, word(target))

    if isinstance(expr, AndExpr):
        q, r, q_inv, r_inv = COMMUTATORS[target]
        return (
            expand(expr.left, q)
            + expand(expr.right, r)
            + expand(expr.left, q_inv)
            + expand(expr.right, r_inv)
        )

    if isinstance(expr, OrExpr):
        return expand(NotExpr(AndExpr(NotExpr(expr.left), NotExpr(expr.right))), target)

    raise TypeError(expr)


def sequence_perm(lines: list[Line], values: dict[str, int]) -> Perm:
    return perm_product([line.evaluate(values) for line in lines])


def absorb_unconditional(lines: list[Line], suffix: Atom) -> list[Line]:
    if not lines:
        return [Line("*", suffix, suffix)]
    result = list(lines)
    last = result[-1]
    result[-1] = Line(
        last.condition,
        append_word(last.when_one, suffix),
        append_word(last.when_zero, suffix),
    )
    return result


def circuit_fixed_points(values: dict[str, int]) -> list[tuple[int, int, int, int, int, int]]:
    x1, x2, x3 = values["x1"], values["x2"], values["x3"]
    valid: list[tuple[int, int, int, int, int, int]] = []
    for bits in product([0, 1], repeat=6):
        f1, f2, f3, f4, f5, f6 = bits
        if (
            f1 == (x1 and f6)
            and f2 == (x2 or f1)
            and f3 == (x3 and f2)
            and f4 == (x1 or f3)
            and f5 == (x2 and f4)
            and f6 == (x3 or f5)
        ):
            valid.append(bits)
    return valid


def verify_commutators() -> list[str]:
    rows = []
    for target, factors in COMMUTATORS.items():
        got = perm_product([sym_perm(factor) for factor in factors])
        expected = sym_perm(target)
        if got != expected:
            raise AssertionError(f"{target} identity failed: {got} != {expected}")
        rows.append(f"{target} = {''.join(str(factor) for factor in factors)}")
    return rows


def build_functions() -> dict[str, BoolExpr]:
    x1, x2, x3 = VarExpr("x1"), VarExpr("x2"), VarExpr("x3")
    return {
        "f1": AndExpr(x1, OrExpr(x2, x3)),
        "f2": OrExpr(x2, AndExpr(x1, x3)),
        "f3": AndExpr(x3, OrExpr(x1, x2)),
        "f4": OrExpr(x1, AndExpr(x2, x3)),
        "f5": AndExpr(x2, OrExpr(x1, x3)),
        "f6": OrExpr(x3, AndExpr(x1, x2)),
    }


def verify_circuit_formulas(functions: dict[str, BoolExpr]) -> list[list[str]]:
    table = [["x1", "x2", "x3", "f1", "f2", "f3", "f4", "f5", "f6"]]
    for x1, x2, x3 in product([0, 1], repeat=3):
        values = {"x1": x1, "x2": x2, "x3": x3}
        fixed_points = circuit_fixed_points(values)
        if len(fixed_points) != 1:
            raise AssertionError(f"expected one fixed point for {values}, got {fixed_points}")
        expected = fixed_points[0]
        got = tuple(eval_bool(functions[f"f{i}"], values) for i in range(1, 7))
        if got != expected:
            raise AssertionError(f"formula mismatch for {values}: {got} != {expected}")
        table.append([str(x1), str(x2), str(x3), *[str(bit) for bit in got]])
    return table


def verify_sequences(functions: dict[str, BoolExpr], sequences: dict[str, list[Line]]) -> list[list[str]]:
    target_perm = sym_perm(A)
    table = [["function", "lines", "verification"]]
    for name, expr in functions.items():
        lines = sequences[name]
        for x1, x2, x3 in product([0, 1], repeat=3):
            values = {"x1": x1, "x2": x2, "x3": x3}
            expected = target_perm if eval_bool(expr, values) else ID
            got = sequence_perm(lines, values)
            if got != expected:
                raise AssertionError(
                    f"{name} failed for {values}: got {got}, expected {expected}"
                )
        table.append([name, str(len(lines)), "PASS: A iff function=1, * iff function=0"])
    return table


def write_text_solution(
    path: Path,
    identities: list[str],
    functions: dict[str, BoolExpr],
    sequences: dict[str, list[Line]],
    truth_table: list[list[str]],
    sequence_table: list[list[str]],
) -> None:
    with path.open("w", encoding="utf-8") as f:
        f.write("EE 5393 Homework 4 - Conditional Permutation Solution\n")
        f.write("Target permutation for every function: A\n\n")
        f.write("Conventions:\n")
        f.write("  The five-number notation is cycle notation, as in the homework.\n")
        f.write("  Products are read left-to-right, matching A = CBC'B' in the handout.\n\n")
        f.write("Base permutations:\n")
        for name in ["A", "B", "C", "D", "E"]:
            f.write(f"  {name} = {BASE_CYCLES[name]}\n")
        f.write("\nVerified commutator identities:\n")
        for row in identities:
            f.write(f"  {row}\n")
        f.write("\nCircuit functions:\n")
        for name, expr in functions.items():
            f.write(f"  {name} = {expr_text(expr)}\n")
        f.write("\nFeedback simplification:\n")
        f.write("  f6 = x3 + x2(x1 + x3(x2 + x1 f6)) = x3 + x1x2\n")
        f.write("  The other five formulas follow by substitution into f1,...,f5.\n")
        f.write("\nTruth table:\n")
        for row in truth_table:
            f.write("  " + " ".join(row) + "\n")
        f.write("\nSequence verification:\n")
        for row in sequence_table:
            f.write("  " + " | ".join(row) + "\n")
        for name, lines in sequences.items():
            f.write(f"\n{name} = {expr_text(functions[name])}; implement {{{name}: A, *}}\n")
            for idx, line in enumerate(lines, start=1):
                f.write(f"  {idx:02d}. {line.text()}\n")
        f.write(f"\nSource link: {SOURCE_LINK}\n")


def make_table(data: list[list[str]], font_size: int = 8) -> Table:
    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eef7")),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#8090a0")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), font_size),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    return table


def write_pdf_solution(
    path: Path,
    identities: list[str],
    functions: dict[str, BoolExpr],
    sequences: dict[str, list[Line]],
    truth_table: list[list[str]],
    sequence_table: list[list[str]],
) -> None:
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=0.55 * inch,
        rightMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="CenterTitle", parent=styles["Title"], alignment=TA_CENTER))
    mono = ParagraphStyle(
        "Mono",
        parent=styles["Code"],
        fontName="Courier",
        fontSize=8.3,
        leading=10.2,
        leftIndent=8,
    )
    small = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontSize=8.5,
        leading=10.5,
    )

    story = []
    story.append(Paragraph("EE 5393 Homework 4", styles["CenterTitle"]))
    story.append(Paragraph("Conditional Permutation Implementation", styles["Heading2"]))
    story.append(
        Paragraph(
            "Each function below is implemented as {function: A, *}. "
            "Thus the resulting permutation is A exactly when the Boolean function is 1, "
            "and identity * exactly when the function is 0.",
            styles["BodyText"],
        )
    )
    story.append(
        Paragraph(
            "Convention: the five-number notation is cycle notation, and products are "
            "read left-to-right, matching the handout identities such as A = CBC'B'.",
            styles["BodyText"],
        )
    )
    story.append(Spacer(1, 6))
    story.append(Paragraph("Base permutations", styles["Heading3"]))
    story.append(
        Preformatted(
            "\n".join(f"{name} = {BASE_CYCLES[name]}" for name in ["A", "B", "C", "D", "E"]),
            mono,
        )
    )
    story.append(Paragraph("Verified identities", styles["Heading3"]))
    story.append(Preformatted("\n".join(identities), mono))
    story.append(Paragraph("Circuit equations and simplified functions", styles["Heading3"]))
    equations = [
        "f1 = x1 f6",
        "f2 = x2 + f1",
        "f3 = x3 f2",
        "f4 = x1 + f3",
        "f5 = x2 f4",
        "f6 = x3 + f5",
        "",
        "Feedback simplification:",
        "f6 = x3 + x2(x1 + x3(x2 + x1 f6)) = x3 + x1x2",
        "The other five formulas follow by substitution.",
        "",
        *[f"{name} = {expr_text(expr)}" for name, expr in functions.items()],
    ]
    story.append(Preformatted("\n".join(equations), mono))
    story.append(PageBreak())
    story.append(Paragraph("Truth-table check from the circuit fixed point", styles["Heading3"]))
    story.append(make_table(truth_table, font_size=7.7))
    story.append(Spacer(1, 6))
    story.append(Paragraph("Sequence verification", styles["Heading3"]))
    story.append(make_table(sequence_table, font_size=7.7))
    story.append(PageBreak())

    for idx, (name, expr) in enumerate(functions.items(), start=1):
        story.append(Paragraph(f"{name}: {expr_text(expr)}", styles["Heading2"]))
        story.append(
            Paragraph(
                f"Expansion of {{{name}: A, *}}. Line count: {len(sequences[name])}.",
                small,
            )
        )
        listing = "\n".join(f"{i:02d}. {line.text()}" for i, line in enumerate(sequences[name], start=1))
        story.append(Preformatted(listing, mono))
        if idx != len(functions):
            story.append(PageBreak())

    doc.build(story, canvasmaker=LinkCanvas)


def main() -> None:
    outdir = Path(__file__).resolve().parent
    identities = verify_commutators()
    functions = build_functions()
    truth_table = verify_circuit_formulas(functions)
    sequences = {name: expand(expr, A) for name, expr in functions.items()}
    sequence_table = verify_sequences(functions, sequences)

    text_path = outdir / "hw4_solution.txt"
    pdf_path = outdir / "hw4.pdf"
    write_text_solution(text_path, identities, functions, sequences, truth_table, sequence_table)
    write_pdf_solution(pdf_path, identities, functions, sequences, truth_table, sequence_table)

    print("Verified commutator identities: PASS")
    print("Verified circuit formulas against fixed-point equations: PASS")
    print("Verified all conditional-permutation sequences: PASS")
    print(f"Wrote {text_path}")
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
