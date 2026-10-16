"""A Transformer encoder block as a list of operators with shapes.

The model is deliberately small: each operator knows its shape, how many
arithmetic operations it performs and how many bytes it must move at minimum
(every operand read once, every output written once). Real traffic is higher;
Lab 1 shows by how much once the on-chip buffer is finite.

Conventions
-----------
* A GEMM has shape (M, K, N): an (M x K) matrix times a (K x N) matrix.
  One multiply-accumulate (MAC) counts as 2 operations.
* ``count`` replicates an operator, e.g. one attention GEMM per head.
* Element-wise and row-wise operators have shape (rows, cols).
"""

from __future__ import annotations

from dataclasses import dataclass

# Primitive operations per element for the non-linear and element-wise ops,
# using the textbook formulations (see archsim.nonlinear for the code).
# exp, tanh, div and rsqrt are counted as one operation each here; their real
# cost is much higher and is handled in archsim.energy.
ELEMENTWISE_OPS = {
    # max-compare, subtract max, exp, running sum, divide
    "softmax": {"cmp": 1, "add": 2, "exp": 1, "div": 1},
    # 0.5 * x * (1 + tanh(sqrt(2/pi) * (x + 0.044715 x^3)))
    "gelu": {"mul": 6, "add": 2, "tanh": 1},
    # mean, centre, square, variance sum, scale by rsqrt, affine
    "layernorm": {"add": 4, "mul": 3, "rsqrt": 1},
    "add": {"add": 1},
}

VIT_TINY = dict(seq=197, dim=192, heads=3, mlp_ratio=4, depth=12)


@dataclass(frozen=True)
class Op:
    name: str
    kind: str  # "gemm" or a key of ELEMENTWISE_OPS
    shape: tuple
    count: int = 1
    weights: bool = False  # GEMM whose right operand is a stored weight matrix
    n_inputs: int = 1  # element-wise inputs (2 for a residual add)

    @property
    def is_gemm(self) -> bool:
        return self.kind == "gemm"

    @property
    def macs(self) -> int:
        if not self.is_gemm:
            return 0
        m, k, n = self.shape
        return m * k * n * self.count

    @property
    def elements(self) -> int:
        """Output elements (all instances)."""
        if self.is_gemm:
            m, _, n = self.shape
            return m * n * self.count
        rows, cols = self.shape
        return rows * cols * self.count

    def primitive_ops(self) -> dict:
        """Primitive operation counts, e.g. {"mul": ..., "add": ..., "exp": ...}."""
        if self.is_gemm:
            return {"mac": self.macs}
        per_elem = ELEMENTWISE_OPS[self.kind]
        ops = {k: v * self.elements for k, v in per_elem.items()}
        if self.kind == "layernorm":
            ops["rsqrt"] = self.shape[0] * self.count  # one per row, not per element
        return ops

    @property
    def flops(self) -> int:
        if self.is_gemm:
            return 2 * self.macs
        return sum(self.primitive_ops().values())

    def bytes(self, bits: int = 8) -> int:
        """Minimum memory traffic in bytes: each operand read once, output written once."""
        b = bits / 8
        if self.is_gemm:
            m, k, n = self.shape
            return int((m * k + k * n + m * n) * self.count * b)
        return int(self.elements * (self.n_inputs + 1) * b)

    def intensity(self, bits: int = 8) -> float:
        """Operations per byte at minimum traffic."""
        return self.flops / self.bytes(bits)


def vit_block(seq: int = 197, dim: int = 192, heads: int = 3, mlp_ratio: int = 4) -> list[Op]:
    """One pre-norm Transformer encoder block (ViT-Tiny defaults)."""
    if dim % heads:
        raise ValueError("dim must be divisible by heads")
    dh = dim // heads
    hidden = mlp_ratio * dim
    return [
        Op("ln1", "layernorm", (seq, dim)),
        Op("qkv", "gemm", (seq, dim, 3 * dim), weights=True),
        Op("scores", "gemm", (seq, dh, seq), count=heads),  # Q K^T
        Op("softmax", "softmax", (seq, seq), count=heads),
        Op("context", "gemm", (seq, seq, dh), count=heads),  # P V
        Op("proj", "gemm", (seq, dim, dim), weights=True),
        Op("add1", "add", (seq, dim), n_inputs=2),
        Op("ln2", "layernorm", (seq, dim)),
        Op("fc1", "gemm", (seq, dim, hidden), weights=True),
        Op("gelu", "gelu", (seq, hidden)),
        Op("fc2", "gemm", (seq, hidden, dim), weights=True),
        Op("add2", "add", (seq, dim), n_inputs=2),
    ]


def weight_count(ops: list[Op]) -> int:
    """Number of GEMM weight parameters (biases and LayerNorm affine ignored)."""
    return sum(op.shape[1] * op.shape[2] * op.count for op in ops if op.weights)


def summary(ops: list[Op], bits: int = 8) -> list[dict]:
    """One row per operator with FLOPs, bytes and their share of the block total."""
    total_f = sum(op.flops for op in ops)
    total_b = sum(op.bytes(bits) for op in ops)
    rows = []
    for op in ops:
        f, b = op.flops, op.bytes(bits)
        rows.append(dict(name=op.name, kind=op.kind, flops=f, bytes=b,
                         flops_pct=100 * f / total_f, bytes_pct=100 * b / total_b,
                         intensity=f / b))
    return rows


def print_summary(ops: list[Op], bits: int = 8) -> None:
    print(f"{'op':<9}{'kind':<10}{'MFLOP':>9}{'%':>6}{'kB':>9}{'%':>6}{'FLOP/B':>8}")
    for r in summary(ops, bits):
        print(f"{r['name']:<9}{r['kind']:<10}{r['flops'] / 1e6:>9.2f}{r['flops_pct']:>6.1f}"
              f"{r['bytes'] / 1e3:>9.1f}{r['bytes_pct']:>6.1f}{r['intensity']:>8.1f}")
