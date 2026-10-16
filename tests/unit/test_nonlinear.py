import numpy as np
import pytest

from archsim import nonlinear as nl

x = np.linspace(-6, 6, 241)


def test_softmax_rows_sum_to_one():
    s = nl.softmax(np.random.default_rng(0).normal(size=(5, 7)))
    assert np.allclose(s.sum(axis=-1), 1)


def test_gelu_reference_values():
    assert nl.gelu(np.array([0.0]))[0] == 0
    assert nl.gelu(np.array([1.0]))[0] == pytest.approx(0.8413447, rel=1e-6)


@pytest.mark.parametrize("fn,tol", [(nl.gelu_tanh, 1e-3), (nl.gelu_sigmoid, 0.03), (nl.gelu_ibert, 0.02)])
def test_gelu_approximations(fn, tol):
    assert nl.error_stats(fn(x), nl.gelu(x))["max_abs"] < tol


def test_exp_ibert():
    z = np.linspace(-10, 0, 101)
    assert nl.error_stats(nl.exp_ibert(z), np.exp(z))["max_abs"] < 5e-3


def test_softmax_ibert_close_to_exact():
    s = np.random.default_rng(1).normal(scale=3, size=(8, 16))
    assert np.abs(nl.softmax_ibert(s) - nl.softmax(s)).max() < 5e-3


def test_counter_and_energy():
    ops = nl.OpCounter()
    nl.softmax(np.zeros((2, 3)), ops=ops)
    assert ops.counts["exp"] == 6 and ops.counts["div"] == 6
    int_ops = nl.OpCounter()
    nl.softmax_ibert(np.zeros((2, 3)), ops=int_ops)
    assert int_ops.counts["div"] == 2
    # the integer version should be far cheaper per element
    assert int_ops.energy_pj(16) < ops.energy_pj(32) / 5


def test_layernorm():
    y = nl.layernorm(np.random.default_rng(2).normal(size=(4, 32)))
    assert np.allclose(y.mean(axis=-1), 0, atol=1e-7)
    assert np.allclose(y.std(axis=-1), 1, atol=1e-3)


def test_attention_with_plugged_softmax():
    rng = np.random.default_rng(3)
    Q, K, V = rng.normal(size=(3, 6, 4))
    ref = nl.attention(Q, K, V)
    approx = nl.attention(Q, K, V, nl.softmax_ibert)
    assert np.abs(ref - approx).max() < 1e-2
