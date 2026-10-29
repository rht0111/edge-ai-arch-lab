"""A toy coarse-grained reconfigurable array (CGRA).

A size x size mesh of PEs, each able to run one word-level operation per
cycle and to pass a value to a neighbour in one cycle per hop. A small
dataflow graph (DFG) is placed and scheduled greedily, operation by operation
in topological order. Each operation goes to the PE where it can start
earliest, accounting for the hops its operands need.

This is a teaching model, not a compiler. It has no modulo scheduling, no
register pressure and unlimited routing bandwidth. It is enough to show the two costs a
CGRA pays for flexibility, routing hops and per-operation configuration,
against a fixed-function unit for the same graph.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import math

from . import energy

HOP_PJ = 0.05      # assumed, one 16-bit word over one PE-to-PE link
CONFIG_PJ = 0.1    # assumed, per-operation context or instruction fetch
PE_AREA_UM2 = 3000.0  # assumed, 16-bit ALU + multiplier + registers + switch


@dataclass(frozen=True)
class Node:
    name: str
    op: str          # add, mul, shift, cmp, floor, lut
    inputs: tuple = ()


@dataclass
class Mapping:
    size: int
    place: dict = field(default_factory=dict)   # node -> (row, col)
    start: dict = field(default_factory=dict)   # node -> cycle
    hops: int = 0
    cycles: int = 0
    energy_pj: float = 0.0
    pipelined: bool = False

    @property
    def graphs_per_cycle(self) -> float:
        """Steady-state throughput when the same graph is applied to a stream of inputs."""
        return 1.0 if self.pipelined else 1.0 / self.cycles

    @property
    def n_ops(self) -> int:
        return len(self.place)

    @property
    def utilization(self) -> float:
        """Fraction of PE-cycles doing useful work in steady state."""
        return self.n_ops * self.graphs_per_cycle / self.size ** 2

    @property
    def res_mii(self) -> int:
        """Resource-limited initiation interval if the graph were software-pipelined."""
        return math.ceil(self.n_ops / self.size ** 2)


def _dist(p, q) -> int:
    return abs(p[0] - q[0]) + abs(p[1] - q[1])


def map_dfg(dfg: list[Node], size: int = 4, bits: int = 16, pipelined: bool = False) -> Mapping:
    """Place and schedule ``dfg``. Graph inputs enter on the west edge of every row.

    By default the mapper minimises the latency of one graph and may stack
    dependent operations on the same PE. With ``pipelined=True`` every PE runs
    a single operation (a spatial pipeline), so a new graph can start every
    cycle at the price of more hops. The graph must fit on size x size PEs.
    """
    if pipelined and len(dfg) > size * size:
        raise ValueError(f"{len(dfg)} operations do not fit on {size * size} PEs")
    names = {n.name for n in dfg}
    pes = [(r, c) for r in range(size) for c in range(size)]
    busy: set[tuple] = set()          # (pe, cycle)
    used: set[tuple] = set()
    mp = Mapping(size, pipelined=pipelined)
    for node in dfg:
        best = None
        for pe in pes:
            if pipelined and pe in used:
                continue
            ready, hops = 0, 0
            for src in node.inputs:
                if src in names:
                    d = _dist(mp.place[src], pe)
                    ready = max(ready, mp.start[src] + 1 + d)
                else:                 # external input from the west edge
                    d = pe[1]
                    ready = max(ready, d)
                hops += d
            t = ready
            while (pe, t) in busy:
                t += 1
            key = (t, hops, pe)
            if best is None or key < best:
                best = key
        t, hops, pe = best
        busy.add((pe, t))
        used.add(pe)
        mp.place[node.name], mp.start[node.name] = pe, t
        mp.hops += hops
    mp.cycles = max(mp.start.values()) + 1
    ops = sum(energy.op_energy(n.op, bits) for n in dfg)
    mp.energy_pj = ops + mp.hops * HOP_PJ + len(dfg) * CONFIG_PJ
    return mp


def fixed_function(dfg: list[Node], bits: int = 16) -> dict:
    """Same graph as a hard-wired pipeline, with no hops and no configuration energy."""
    depth = {}
    for n in dfg:
        depth[n.name] = 1 + max((depth.get(s, 0) for s in n.inputs), default=0)
    area = sum(energy.AREA_UM2.get((n.op, bits), energy.AREA_UM2[("add", bits)]) for n in dfg)
    return dict(latency=max(depth.values()), throughput=1.0,
                energy_pj=sum(energy.op_energy(n.op, bits) for n in dfg), area_um2=area)


def replicate(dfg: list[Node], copies: int) -> list[Node]:
    """``copies`` independent instances, e.g. to process several elements at once."""
    out = []
    for i in range(copies):
        rename = {n.name: f"{n.name}{i}" for n in dfg}
        for n in dfg:
            ins = tuple(rename.get(s, f"{s}{i}") for s in n.inputs)
            out.append(Node(rename[n.name], n.op, ins))
    return out


# --- example graphs ----------------------------------------------------------

def dfg_exp_shift() -> list[Node]:
    """exp(x) = 2^(x log2 e) with 2^f ~ 1 + f, the shift-based exp of Lab 3."""
    return [
        Node("y", "mul", ("x",)),        # y = x * log2(e)
        Node("z", "floor", ("y",)),
        Node("f", "add", ("y", "z")),    # f = y - z
        Node("m", "add", ("f",)),        # 1 + f
        Node("e", "shift", ("m", "z")),  # (1 + f) << z
    ]


def dfg_gelu_ibert() -> list[Node]:
    return [
        Node("u", "mul", ("x",)), Node("au", "cmp", ("u",)),          # |x / sqrt 2|
        Node("cl", "cmp", ("au",)), Node("t", "add", ("cl",)),        # min(., -b) + b
        Node("t2", "mul", ("t", "t")), Node("at2", "mul", ("t2",)),
        Node("p", "add", ("at2",)), Node("s", "mul", ("p", "x")),     # sign via multiply
        Node("one", "add", ("s",)), Node("hx", "mul", ("x",)), Node("g", "mul", ("hx", "one")),
    ]


def dfg_dot(n: int = 4) -> list[Node]:
    nodes = [Node(f"p{i}", "mul", (f"a{i}", f"b{i}")) for i in range(n)]
    level, k = [f"p{i}" for i in range(n)], 0
    while len(level) > 1:
        nxt = []
        for i in range(0, len(level) - 1, 2):
            nodes.append(Node(f"s{k}", "add", (level[i], level[i + 1])))
            nxt.append(f"s{k}")
            k += 1
        if len(level) % 2:
            nxt.append(level[-1])
        level = nxt
    return nodes


def draw(mp: Mapping, dfg: list[Node], ax=None):
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots(figsize=(4, 4))
    n = mp.size
    for r in range(n):
        for c in range(n):
            ax.add_patch(plt.Rectangle((c, n - 1 - r), 0.95, 0.95, fill=False, color="grey"))
    labels: dict = {}
    for node in dfg:
        r, c = mp.place[node.name]
        labels.setdefault((r, c), []).append(f"{node.op} @{mp.start[node.name]}")
    for (r, c), lines in labels.items():
        ax.text(c + 0.47, n - 1 - r + 0.47, "\n".join(lines), ha="center", va="center", fontsize=7)
    for node in dfg:
        for s in node.inputs:
            if s in mp.place:
                (r0, c0), (r1, c1) = mp.place[s], mp.place[node.name]
                ax.annotate("", (c1 + 0.47, n - 1 - r1 + 0.47), (c0 + 0.47, n - 1 - r0 + 0.47),
                            arrowprops=dict(arrowstyle="->", color="C0", alpha=0.5))
    ax.set_xlim(0, n)
    ax.set_ylim(0, n)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"{mp.n_ops} ops, {mp.cycles} cycles, {mp.hops} hops")
    return ax
