import json
import math

import pytest

from archsim import design
from archsim.design import Design, evaluate


def test_default_design_is_sane():
    m = evaluate(Design())
    assert m["latency_ms"] > 0 and m["energy_uj"] > 0
    assert m["area_mm2"] == pytest.approx(sum(m["area_breakdown_mm2"].values()))
    assert m["energy_uj"] == pytest.approx(sum(m["energy_breakdown_uj"].values()))


def test_weights_bound_dram_energy_from_below():
    # every weight crosses the DRAM link at least once per inference
    from archsim import energy, workloads
    w = workloads.weight_count(workloads.vit_block()) * 12
    m = evaluate(Design(buffer_kib=4096))
    assert m["energy_breakdown_uj"]["dram"] >= energy.dram_energy(w) * 1e-6


def test_more_buffer_less_dram():
    small = evaluate(Design(buffer_kib=32))["energy_breakdown_uj"]["dram"]
    large = evaluate(Design(buffer_kib=256))["energy_breakdown_uj"]["dram"]
    assert large < small


def test_units_cut_latency_and_add_area():
    base, units = evaluate(Design()), evaluate(Design(softmax_lanes=8, gelu_lanes=8))
    assert units["latency_ms"] < base["latency_ms"] / 2
    assert units["area_mm2"] > base["area_mm2"]


def test_precision_trends():
    e = {b: evaluate(Design(bits=b))["energy_uj"] for b in (4, 8, 16)}
    assert e[4] < e[8] < e[16]
    assert evaluate(Design(bits=4))["notes"]


def test_fps_at_budget_consistent_with_power():
    m = evaluate(Design(softmax_lanes=8, gelu_lanes=8))
    fps = m["fps_at_1mw"]
    p = evaluate(Design(softmax_lanes=8, gelu_lanes=8), fps=fps)["power_mw"]
    assert p == pytest.approx(design.POWER_BUDGET_MW, rel=1e-6)


def test_cannot_sustain_frame_rate():
    assert math.isnan(evaluate(Design(array=4), fps=100)["power_mw"])


def test_validation():
    with pytest.raises(ValueError):
        evaluate(Design(bits=3))


def test_submission_roundtrip(tmp_path):
    sub = design.make_submission("team-a", Design(array=8))
    p = design.save_submission(sub, tmp_path / "s.json")
    raw = json.loads(open(p).read())
    raw["metrics"]["energy_uj"] = 1.0          # tampering is undone on load
    open(p, "w").write(json.dumps(raw))
    again = design.load_submission(p)
    assert again["metrics"] == pytest.approx(sub["metrics"])
