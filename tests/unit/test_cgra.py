from archsim import cgra


def _respects_dependencies(dfg, mp):
    for n in dfg:
        for s in n.inputs:
            if s in mp.start:
                assert mp.start[n.name] > mp.start[s]


def test_dot_product_mapping():
    dfg = cgra.dfg_dot(4)
    mp = cgra.map_dfg(dfg)
    assert mp.n_ops == 7
    _respects_dependencies(dfg, mp)
    # three levels of operations at least
    assert mp.cycles >= 3
    assert len(set(mp.place.values())) <= 16


def test_one_op_per_pe_per_cycle():
    dfg = cgra.replicate(cgra.dfg_exp_shift(), 6)
    mp = cgra.map_dfg(dfg)
    slots = [(mp.place[n.name], mp.start[n.name]) for n in dfg]
    assert len(slots) == len(set(slots))
    _respects_dependencies(dfg, mp)
    assert mp.res_mii == 2


def test_cgra_costs_more_energy_than_fixed_function():
    dfg = cgra.dfg_gelu_ibert()
    mp = cgra.map_dfg(dfg)
    ff = cgra.fixed_function(dfg)
    assert mp.energy_pj > ff["energy_pj"]
    assert ff["latency"] <= mp.cycles
    assert 0 < mp.utilization <= 1
