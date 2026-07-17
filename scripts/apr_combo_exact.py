"""
apr_combo_exact.py - APR del TAA Combo con los pesos EXACTOS de TradingView
(CBOE_DLY_SPX, 1D.csv), no la reconstruccion. Misma spec que apr_combo.py:
chequeo semanal (primer dia ISO) + banda 8%, leakage-free, coste 10 bps, rf=0,
null de timing DIARIO leakage-free (corregido: sin el look-ahead del null semanal).
Reusa build_weights de backtest_taa. Solo ASCII.
"""
import numpy as np
import pandas as pd
import backtest_taa as bt
from apr_combo import sim, ratios, sh, cg, ASSETS, BAND, COST

COMPONENTS = ["2_DefenseFirst", "4_Blend50_50", "1_SPY_or_Cash"]


def main():
    np.random.seed(42)
    sig, p = bt.load()
    m = pd.merge(sig, p, on="date", how="inner").sort_values("date").reset_index(drop=True)
    W = bt.build_weights(m)
    tgt = sum(W[c][ASSETS].values for c in COMPONENTS) / len(COMPONENTS)   # combo exacto = media de las 3
    R = m[["PX_" + a for a in ASSETS]].pct_change().values
    yrs = m["date"].dt.year.values
    oos = (m["date"] >= "2025-01-01").values
    ic = m["date"].dt.isocalendar(); wk = ic.week.values + ic.year.values * 100
    check = np.r_[True, wk[1:] != wk[:-1]]

    net, tn, nr = sim(tgt, R, check)
    r0 = ratios(net)
    print("=== APR TAA COMBO EXACTO (pesos TradingView CBOE_DLY_SPX 1D.csv) ===")
    print("Ventana %s..%s | N=%d | semanal primer dia ISO + banda %.0f%% | net %.0f bps | turnover %.3fx | reb/ano %.3f"
          % (m["date"][np.isfinite(net)].min().date(), m["date"].max().date(),
             np.isfinite(net).sum(), BAND, COST, tn, nr))
    for k, v in r0.items():
        print("  %-7s %.6f" % (k, v))
    print("  IS(<=2024) CAGR %.4f Sharpe %.6f | OOS(>=2025) CAGR %.4f Sharpe %.6f"
          % (cg(net[~oos]), sh(net[~oos]), cg(net[oos]), sh(net[oos])))
    print("  por ano:", {int(y): round((np.prod(1 + net[(yrs == y) & np.isfinite(net)]) - 1) * 100, 1)
                          for y in sorted(set(yrs)) if ((yrs == y) & np.isfinite(net)).sum() > 20})

    rr = net[np.isfinite(net)]; NB = 2000
    iid = np.array([sh(rr[np.random.randint(0, len(rr), len(rr))]) for _ in range(NB)])
    mon = (m["date"].dt.year * 12 + m["date"].dt.month).values[np.isfinite(net)]
    blk = [rr[mon == u] for u in np.unique(mon)]
    bb = np.array([sh(np.concatenate([blk[i] for i in np.random.randint(0, len(blk), len(blk))])) for _ in range(NB)])
    print("  bootstrap Sharpe CI95 iid [%.4f, %.4f] | bloque-mes [%.4f, %.4f]"
          % (np.percentile(iid, 2.5), np.percentile(iid, 97.5), np.percentile(bb, 2.5), np.percentile(bb, 97.5)))

    tgt0 = tgt
    wids = [u for u in np.unique(wk) if np.isfinite(tgt0[np.where(wk == u)[0][0], 0])]
    wkix = {u: i for i, u in enumerate(wids)}
    Tw = np.array([tgt0[np.where(wk == u)[0][0]] for u in wids])
    dayw = np.array([wkix.get(wk[t], -1) for t in range(len(m))])

    def null_sharpe(assign):
        Td = np.full((len(m), 6), np.nan); ok = dayw >= 0
        Td[ok] = Tw[assign[dayw[ok]]]
        wl = np.roll(Td, 1, axis=0); wl[0] = np.nan
        rd = np.nansum(wl * R, axis=1); mk = np.isfinite(rd) & (dayw > 0)
        return rd[mk].mean() / rd[mk].std(ddof=1) * np.sqrt(252)

    real = null_sharpe(np.arange(len(wids)))
    nul = np.array([null_sharpe(np.random.permutation(len(wids))) for _ in range(NB)])
    print("  NULL timing diario leakage-free: Sharpe real %.4f | null %.4f +- %.4f | p(null>=real)=%.4f"
          % (real, nul.mean(), nul.std(), (nul >= real).mean()))

    print("  sens banda 5/8/12%%: %.4f / %.4f / %.4f | coste 5/10/20 bps: %.4f / %.4f / %.4f"
          % (ratios(sim(tgt, R, check, 5)[0])["Sharpe"], r0["Sharpe"], ratios(sim(tgt, R, check, 12)[0])["Sharpe"],
             ratios(sim(tgt, R, check, 8, 5)[0])["Sharpe"], r0["Sharpe"], ratios(sim(tgt, R, check, 8, 20)[0])["Sharpe"]))


if __name__ == "__main__":
    main()
