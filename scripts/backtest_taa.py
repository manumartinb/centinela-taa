"""
backtest_taa.py - Backtest de las 4 estrategias TAA del CSV de TradingView
(CBOE_DLY_SPX, 1D.csv) sobre precios adjusted (total-return) reales de los ETFs.

Estrategias identificadas (columnas del CSV, por indice para evitar el emoji):
  1. SPY-or-Cash: regimen (col5, 0/1) -> 100% SPY / 100% SHV(cash).
  2. Defense First (base): pesos QQQ/SHV/TLT/DBC/GLD (cols 12-16, suman 1).
  3. HAA: peso QQQ = col18; defensa (1-QQQ) repartida en la MISMA proporcion
     SHV/TLT/DBC/GLD que la base (reconstruccion, ver nota).
  4. Blend 50/50: peso QQQ = col20; misma reconstruccion de defensa.

Leakage-free: retorno[t] = sum(w_asset[t-1] * ret_asset[t]). Coste por turnover.
Reglas del proyecto: ASCII puro.
"""

import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.abspath(__file__))
CSV = r"C:\Users\Administrator\Desktop\CBOE_DLY_SPX, 1D.csv"
ETF = os.path.join(BASE, "ANALISIS", "OUTPUT", "data", "etf_adjclose.csv")
OUT = os.path.join(BASE, "ANALISIS", "OUTPUT", "data")
COST_BPS = 5.0   # coste por unidad de turnover (one-way), bps


def load():
    d = pd.read_csv(CSV, encoding="utf-8", errors="replace") if False else pd.read_csv(CSV, encoding="latin-1")
    d["date"] = pd.to_datetime(d["time"])
    reg = pd.to_numeric(d.iloc[:, 5], errors="coerce")
    cols = {a: pd.to_numeric(d.iloc[:, i], errors="coerce") for a, i in
            [("QQQ", 12), ("SHV", 13), ("TLT", 14), ("DBC", 15), ("GLD", 16),
             ("QQQ_HAA", 18), ("QQQ_BLEND", 20)]}
    sig = pd.DataFrame({"date": d["date"], "reg": reg, **cols})
    p = pd.read_csv(ETF); p["date"] = pd.to_datetime(p["date"])
    p = p.rename(columns={t: "PX_" + t for t in p.columns if t != "date"})
    return sig, p


def build_weights(sig):
    """Devuelve dict estrategia -> DataFrame de pesos (columnas = assets)."""
    ASSETS = ["QQQ", "SHV", "TLT", "DBC", "GLD", "SPY"]
    W = {}
    n = len(sig)
    # 1. SPY-or-Cash
    w = pd.DataFrame(0.0, index=sig.index, columns=ASSETS)
    w["SPY"] = sig["reg"]; w["SHV"] = 1 - sig["reg"]
    W["1_SPY_or_Cash"] = w
    # 2. Defense First (base)
    w = pd.DataFrame(0.0, index=sig.index, columns=ASSETS)
    for a in ["QQQ", "SHV", "TLT", "DBC", "GLD"]:
        w[a] = sig[a]
    W["2_DefenseFirst"] = w
    # 3/4. reconstruir con QQQ variante + defensa proporcional a la base
    def_base = sig[["SHV", "TLT", "DBC", "GLD"]].copy()
    def_sum = def_base.sum(axis=1).replace(0, np.nan)
    for name, qcol in [("3_HAA", "QQQ_HAA"), ("4_Blend50_50", "QQQ_BLEND")]:
        w = pd.DataFrame(0.0, index=sig.index, columns=ASSETS)
        q = sig[qcol].clip(0, 1)
        w["QQQ"] = q
        scale = (1 - q) / def_sum
        for a in ["SHV", "TLT", "DBC", "GLD"]:
            w[a] = (def_base[a] * scale).fillna(0.0)
        # si def_sum era 0 (base 100% QQQ), el resto va a SHV
        allq = (def_sum.isna())
        w.loc[allq, "SHV"] = (1 - q)[allq]
        W[name] = w
    return W


def metrics(r):
    r = r[np.isfinite(r)]
    eq = np.cumprod(1 + r); yrs = len(r) / 252
    cagr = eq[-1] ** (1 / yrs) - 1
    sh = r.mean() / r.std(ddof=1) * np.sqrt(252)
    dn = r[r < 0].std(ddof=1) * np.sqrt(252)
    sortino = (r.mean() * 252) / dn if dn > 0 else np.nan
    dd = (eq / np.maximum.accumulate(eq) - 1).min()
    calmar = cagr / abs(dd) if dd < 0 else np.nan
    return dict(cagr_pct=cagr * 100, sharpe=sh, sortino=sortino, maxdd_pct=dd * 100,
                calmar=calmar, vol_pct=r.std(ddof=1) * np.sqrt(252) * 100)


def bt(weights, rets, cost_bps=COST_BPS):
    """retorno leakage-free + turnover + coste."""
    W = weights.reindex(columns=rets.columns).fillna(0.0).values
    R = rets.values
    n = len(W)
    port = np.full(n, np.nan)
    turn = np.zeros(n)
    for t in range(1, n):
        wp = W[t - 1]
        if np.isnan(R[t]).all() or np.isnan(wp).any():
            continue
        port[t] = np.nansum(wp * R[t])
        turn[t] = np.nansum(np.abs(W[t] - W[t - 1])) / 2.0
    cost = turn * cost_bps / 1e4
    net = port - cost
    ann_turn = np.nanmean(turn) * 252
    return port, net, ann_turn


def main():
    sig, p = load()
    m = pd.merge(sig, p, on="date", how="inner").sort_values("date").reset_index(drop=True)
    assets = ["QQQ", "SHV", "TLT", "DBC", "GLD", "SPY"]
    rets = m[["PX_" + a for a in assets]].pct_change()
    rets.columns = assets
    W = build_weights(m)

    # benchmarks
    bench = {}
    bench["BH_SPY"] = pd.DataFrame({a: (1.0 if a == "SPY" else 0.0) for a in assets}, index=m.index)
    bench["BH_QQQ"] = pd.DataFrame({a: (1.0 if a == "QQQ" else 0.0) for a in assets}, index=m.index)
    w6040 = pd.DataFrame(0.0, index=m.index, columns=assets); w6040["SPY"] = 0.6; w6040["TLT"] = 0.4
    bench["60_40"] = w6040

    rows = []
    series = {}
    for name, w in {**W, **bench}.items():
        gross, net, tn = bt(w, rets)
        mg = metrics(gross); mn = metrics(net)
        rows.append(dict(strategy=name, cagr_gross=mg["cagr_pct"], cagr_net=mn["cagr_pct"],
                         sharpe=mn["sharpe"], sortino=mn["sortino"], maxdd_pct=mn["maxdd_pct"],
                         calmar=mn["calmar"], vol_pct=mn["vol_pct"], ann_turnover=tn))
        series[name] = net
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(OUT, "taa_summary.csv"), index=False)

    # por ano (net) para las 4 estrategias
    yrs = m["date"].dt.year.values
    byyear = {}
    for name in W:
        s = series[name]
        rowy = {}
        for y in sorted(set(yrs)):
            msk = (yrs == y) & np.isfinite(s)
            if msk.sum() > 20:
                rowy[y] = (np.prod(1 + s[msk]) - 1) * 100
        byyear[name] = rowy
    by = pd.DataFrame(byyear).round(1)
    by.to_csv(os.path.join(OUT, "taa_by_year.csv"))

    pd.set_option("display.width", 220); pd.set_option("display.max_columns", 30)
    print("=== BACKTEST TAA (2015-2026, precios adjusted, neto %g bps turnover) ===" % COST_BPS)
    print("Ventana:", m["date"].min().date(), "a", m["date"].max().date(), "| N=%d dias" % len(m))
    print()
    show = ["strategy", "cagr_net", "sharpe", "sortino", "maxdd_pct", "calmar", "vol_pct", "ann_turnover"]
    print(res[show].to_string(index=False, float_format=lambda v: "%.2f" % v))
    print()
    print("=== Retorno por ANO (%, neto) ===")
    print(by.to_string())
    print("\nCSVs en", OUT)


if __name__ == "__main__":
    main()
