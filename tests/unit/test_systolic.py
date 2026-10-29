import numpy as np
import pytest

from archsim import systolic

rng = np.random.default_rng(0)


@pytest.mark.parametrize("m,k,n", [(4, 6, 4), (3, 5, 2), (1, 1, 1), (4, 1, 4), (2, 9, 4)])
def test_os_tile_is_correct_and_matches_formula(m, k, n):
    A, B = rng.integers(-5, 5, (m, k)), rng.integers(-5, 5, (k, n))
    r = systolic.simulate_os_tile(A, B, 4, 4)
    assert np.array_equal(r.out, A @ B)
    assert r.macs == m * k * n
    assert r.cycles == systolic.os_tile_cycles(m, k, n)


@pytest.mark.parametrize("M,k,n", [(6, 4, 4), (5, 3, 2), (1, 1, 1), (10, 4, 1)])
def test_ws_tile_is_correct(M, k, n):
    A, W = rng.integers(-5, 5, (M, k)), rng.integers(-5, 5, (k, n))
    r = systolic.simulate_ws_tile(A, W, 4, 4)
    assert np.array_equal(r.out, A @ W)
    assert r.macs == M * k * n
    assert r.load_cycles == k


@pytest.mark.parametrize("dataflow", ["os", "ws"])
def test_matmul_on_awkward_shape(dataflow):
    A, B = rng.normal(size=(13, 7)), rng.normal(size=(7, 6))
    C, cycles = systolic.matmul(A, B, 4, 4, dataflow)
    assert np.allclose(C, A @ B)
    assert cycles == systolic.gemm(13, 7, 6, 4, 4, dataflow)["cycles"]


def test_utilization_bounded_and_shape_sensitive():
    full = systolic.gemm(64, 64, 64, 4, 4, "os")["utilization"]
    awkward = systolic.gemm(65, 64, 64, 4, 4, "os")["utilization"]
    assert 0 < awkward < full < 1
    assert systolic.gemm(64, 64, 64, 4, 4)["cycles"] >= systolic.ideal_cycles(64, 64, 64, 4, 4)


def test_trace_frames():
    r = systolic.simulate_os_tile(np.ones((4, 3)), np.ones((3, 4)), trace=True)
    assert len(r.frames) == r.cycles
    assert sum(f["active"].sum() for f in r.frames) == r.macs


def test_ws_trace_covers_every_cycle_including_weight_loading():
    from archsim import viz
    r = systolic.simulate_ws_tile(np.ones((6, 3)), np.ones((3, 4)), 4, 4, trace=True)
    assert len(r.frames) == r.cycles
    assert [f.get("phase") for f in r.frames[:3]] == ["loading weights"] * 3
    assert sum(f["active"].sum() for f in r.frames) == r.macs
    for t in range(r.cycles):           # every slider position must draw
        viz.draw_frame(r, t, dataflow="ws")
