"""
backtest_combo_rebal.py - Combo ganador (1/3 DefenseFirst + 1/3 Blend + 1/3 SPY-or-Cash)
con rebalanceo DIARIO vs SEMANAL vs MENSUAL.

Modelo realista: en el dia de rebalanceo se fija la cartera al peso objetivo (media de las
3 estrategias); entre rebalanceos los pesos DERIVAN con el mercado (no se sigue la senal
diaria). Coste por turnover solo el dia de rebalanceo. Leakage-free (objetivo de hoy -> dia
siguiente). Reglas: ASCII puro.
"""

import os
import numpy as np
import pandas as pd
import backtest_taa as bt

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "ANALISIS", "OUTPUT", "data")
COMPONENTS = ["2_DefenseFirst", "4_Blend50_50", "1_SPY_or_Cash"]


def combo_target(m):
    W = bt.build_weights(m)
    assets = W[COMPONENTS[0]].columns
    tgt = sum(W[c][assets].values for c in COMPONENTS) / len(COMPONENTS)
    return pd.DataFrame(tgt, columns=assets, index=m.index)


def rebal_mask(dates, freq):
    d = pd.to_datetime(dates)
    if freq == "daily":
        return np.ones(len(d), bool)
    if freq == "weekly":
        ic = d.dt.isocalendar()
        wk = ic.week.values + ic.year.values * 100
        return np.r_[wk[:-1] != wk[1:], True]      # ultimo dia de trading de cada semana ISO
    if freq == "monthly":
        mo = d.dt.month.values + d.dt.year.values * 100
        return np.r_[mo[:-1] != mo[1:], True]        # ultimo dia de trading de cada mes
    raise ValueError(freq)


def backtest(target, rets, mask, cost_bps):
    T = target.values
    R = rets.values
    n, k = T.shape
    held = None
    port = np.full(n, np.nan)
    turn = np.zeros(n)     # turnover realizado al cierre del dia t (afecta al dia t+1)
    for t in range(n):
        if held is not None and not np.isnan(R[t]).any():
            port[t] = np.nansum(held * R[t])
            g = held * (1 + R[t]); held = g / g.sum()   # deriva a cierre t
        # decision al cierre t para t+1
        if mask[t] and not np.isnan(T[t]).any():
            if held is None:
                held = T[t].copy()
            else:
                turn[t] = np.nansum(np.abs(T[t] - held)) / 2.0
                held = T[t].copy()
    cost = np.r_[0.0, turn[:-1]] * cost_bps / 1e4       # coste entra el dia siguiente al trade
    net = port - cost
    ann_turn = np.nansum(turn) / (np.isfinite(port).sum() / 252)
    return port, net, ann_turn


def metrics(r, msk=None):
    r = r if msk is None else r[msk]
    r = r[np.isfinite(r)]
    if len(r) < 20:
        return {}
    eq = np.cumprod(1 + r); yrs = len(r) / 252
    cagr = eq[-1] ** (1 / yrs) - 1
    dn = r[r < 0].std(ddof=1) * np.sqrt(252)
    dd = (eq / np.maximum.accumulate(eq) - 1).min()
    return dict(cagr=cagr * 100, sharpe=r.mean() / r.std(ddof=1) * np.sqrt(252),
                sortino=(r.mean() * 252) / dn if dn > 0 else np.nan,
                maxdd=dd * 100, calmar=cagr / abs(dd) if dd < 0 else np.nan)


def main():
    sig, p = bt.load()
    m = pd.merge(sig, p, on="date", how="inner").sort_values("date").reset_index(drop=True)
    assets = ["QQQ", "SHV", "TLT", "DBC", "GLD", "SPY"]
    rets = m[["PX_" + a for a in assets]].pct_change(); rets.columns = assets
    tgt = combo_target(m)[assets]
    oos = (m["date"] >= "2025-01-01").values
    yrs = m["date"].dt.year.values

    print("=== COMBO (1/3 Def + 1/3 Blend + 1/3 SPY-Cash): DIARIO vs SEMANAL vs MENSUAL ===")
    print("Ventana %s a %s\n" % (m["date"].min().date(), m["date"].max().date()))
    byyear_store = {}
    for freq in ["daily", "weekly", "monthly"]:
        mask = rebal_mask(m["date"], freq)
        print("--- %s (rebal/ano ~%d) ---" % (freq.upper(), int(mask.sum() / (len(m) / 252))))
        for cost in [5.0, 10.0, 20.0]:
            _, net, tn = backtest(tgt, rets, mask, cost)
            a = metrics(net); io = metrics(net, ~oos); oo = metrics(net, oos)
            if cost == 5.0:
                byyear_store[freq] = net
            print("   coste %2.0fbps: CAGR %.1f  Sharpe %.2f  Sortino %.2f  Calmar %.2f  MaxDD %5.1f | "
                  "IS Sh %.2f  OOS Sh %.2f  OOS DD %5.1f | turnover %.1fx"
                  % (cost, a["cagr"], a["sharpe"], a["sortino"], a["calmar"], a["maxdd"],
                     io["sharpe"], oo["sharpe"], oo["maxdd"], tn))
        print()

    # por ano (net 10bps) para las 3 frecuencias
    print("=== Retorno por ANO (%, net 10bps) ===")
    rows = {}
    for freq in ["daily", "weekly", "monthly"]:
        mask = rebal_mask(m["date"], freq)
        _, net, _ = backtest(tgt, rets, mask, 10.0)
        rows[freq] = {int(y): (np.prod(1 + net[(yrs == y) & np.isfinite(net)]) - 1) * 100
                      for y in sorted(set(yrs)) if ((yrs == y) & np.isfinite(net)).sum() > 20}
    print(pd.DataFrame(rows).round(1).to_string())
    pd.DataFrame(rows).round(2).to_csv(os.path.join(OUT, "combo_rebal_by_year.csv"))


if __name__ == "__main__":
    main()
