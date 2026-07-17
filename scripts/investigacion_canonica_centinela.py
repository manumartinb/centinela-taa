"""
investigacion_canonica_centinela.py - Investigacion TOTAL para reconfirmar o refutar
CENTINELA (TAA Combo exacto: 1/3 DefenseFirst + 1/3 Blend + 1/3 SPY-or-Cash) como
estrategia canonica para capital real conservador. Pesos EXACTOS de TradingView.

Bateria:
 1. Base + benchmarks (SPY, QQQ, 60/40, EW6, SPX price-only)
 2. Head-to-head vs SPY: alpha/beta, IR, excess mensual (t-test), Sharpe-diff bootstrap
 3. Rolling 12m/36m: % ventanas ganando a SPY (retorno y Sharpe)
 4. Crisis: 2018Q4, COVID 2020, bear 2022, drawdown profundo/duracion underwater
 5. Sub-periodos: 2015-19 / 2020-22 / 2023-26
 6. Sub-estrategias solas vs combo (justificacion del combo)
 7. Estres: delay ejecucion +1d, costes 5-30bps, dia de la semana
Solo ASCII. Config canonica: chequeo semanal (1er dia ISO) + banda 8%, net 10 bps.
"""
import numpy as np
import pandas as pd
import backtest_taa as bt
from apr_combo import sim, ratios, sh, ASSETS

COMP = ["2_DefenseFirst", "4_Blend50_50", "1_SPY_or_Cash"]


def eqw(net):
    r = net[np.isfinite(net)]
    return np.cumprod(1 + r)


def cagr(net):
    r = net[np.isfinite(net)]; e = np.cumprod(1 + r)
    return (e[-1] ** (252 / len(r)) - 1) * 100


def maxdd(net):
    e = eqw(net)
    return ((e / np.maximum.accumulate(e)) - 1).min() * 100


def underwater_days(net):
    e = eqw(net); peak = np.maximum.accumulate(e)
    under = e < peak; best = cur = 0
    for u in under:
        cur = cur + 1 if u else 0
        best = max(best, cur)
    return best


def wret(net, msk):
    r = net[msk & np.isfinite(net)]
    return (np.prod(1 + r) - 1) * 100 if len(r) > 0 else np.nan


def main():
    np.random.seed(42)
    sig, p = bt.load()
    m = pd.merge(sig, p, on="date", how="inner").sort_values("date").reset_index(drop=True)
    W = bt.build_weights(m)
    R = m[["PX_" + a for a in ASSETS]].pct_change().values
    dates = m["date"]; yrs = dates.dt.year.values
    ic = dates.dt.isocalendar(); wk = ic.week.values + ic.year.values * 100
    check = np.r_[True, wk[1:] != wk[:-1]]
    n = len(m)

    tgt = sum(W[c][ASSETS].values for c in COMP) / 3.0
    combo, tn, nreb = sim(tgt, R, check)

    # benchmarks
    def const_w(d):
        t = np.zeros((n, 6))
        for a, v in d.items():
            t[:, ASSETS.index(a)] = v
        return t
    spy = m["PX_SPY"].pct_change().values                      # B&H sin coste
    qqq = m["PX_QQQ"].pct_change().values
    b6040, _, _ = sim(const_w({"SPY": 0.6, "TLT": 0.4}), R, check)
    ew6, _, _ = sim(const_w({a: 1/6 for a in ASSETS}), R, check)
    # SPX price-only (col close del CSV de TradingView; bt.load no la arrastra)
    raw = pd.read_csv(bt.CSV, encoding="latin-1")[["time", "close"]]
    raw["date"] = pd.to_datetime(raw["time"])
    spx = pd.to_numeric(m.merge(raw[["date", "close"]], on="date", how="left")["close"],
                        errors="coerce").pct_change().values

    print("=" * 78)
    print("1. BASE Y BENCHMARKS (ventana %s..%s, N=%d, combo net 10bps)" % (dates.min().date(), dates.max().date(), n))
    print("=" * 78)
    print("%-22s  CAGR  Sharpe Sortino Calmar  MaxDD   Vol  x-veces  underwater(d)" % "serie")
    for nm, s in [("CENTINELA (combo)", combo), ("SPY buy&hold (TR)", spy), ("QQQ buy&hold (TR)", qqq),
                  ("60/40 SPY-TLT", b6040), ("EqualWeight 6", ew6), ("SPX indice (precio)", spx)]:
        r = ratios(s); e = eqw(s)
        print("%-22s %5.1f  %5.2f  %5.2f  %5.2f  %6.1f  %4.1f   x%4.2f     %4d"
              % (nm, r["CAGR"], r["Sharpe"], r["Sortino"], r["Calmar"], r["MaxDD"], r["Vol"], e[-1], underwater_days(s)))

    # ------------------------------------------------------------------ vs SPY
    print()
    print("=" * 78)
    print("2. HEAD-TO-HEAD vs SPY (alineado dia a dia)")
    print("=" * 78)
    ok = np.isfinite(combo) & np.isfinite(spy)
    c, s = combo[ok], spy[ok]
    beta = np.cov(c, s)[0, 1] / np.var(s)
    alpha_d = c.mean() - beta * s.mean()
    ex = c - s
    ir = ex.mean() / ex.std(ddof=1) * np.sqrt(252)
    print("beta vs SPY: %.3f | alpha anualizado: %+.2f%% | Information Ratio: %.2f" % (beta, alpha_d * 252 * 100, ir))
    # excess mensual + t-test
    mon = (dates.dt.year * 100 + dates.dt.month).values[ok]
    dfm = pd.DataFrame({"mon": mon, "c": c, "s": s})
    g = dfm.groupby("mon").apply(lambda x: pd.Series({"c": np.prod(1 + x.c) - 1, "s": np.prod(1 + x.s) - 1}), include_groups=False)
    d = (g["c"] - g["s"]).values
    tstat = d.mean() / (d.std(ddof=1) / np.sqrt(len(d)))
    print("excess mensual medio: %+.2f%% | meses ganando a SPY: %d/%d (%.0f%%) | t-stat=%.2f" % (d.mean() * 100, (d > 0).sum(), len(d), (d > 0).mean() * 100, tstat))
    # Sharpe-diff bootstrap por bloque mensual
    months = sorted(set(mon)); blocks = {u: (dfm[dfm.mon == u].c.values, dfm[dfm.mon == u].s.values) for u in months}
    NB = 2000; diffs = np.empty(NB)
    for i in range(NB):
        pick = np.random.choice(months, len(months), replace=True)
        cc = np.concatenate([blocks[u][0] for u in pick]); ss = np.concatenate([blocks[u][1] for u in pick])
        diffs[i] = sh(cc) - sh(ss)
    print("Sharpe combo - Sharpe SPY = %+.2f | bootstrap CI95 [%+.2f, %+.2f] | p(diff<=0)=%.4f"
          % (sh(c) - sh(s), np.percentile(diffs, 2.5), np.percentile(diffs, 97.5), (diffs <= 0).mean()))

    # ------------------------------------------------------------------ rolling
    print()
    print("=" * 78)
    print("3. VENTANAS RODANTES (combo vs SPY)")
    print("=" * 78)
    ce = pd.Series(np.cumprod(1 + np.nan_to_num(combo)), index=dates)
    se = pd.Series(np.cumprod(1 + np.nan_to_num(spy)), index=dates)
    for lbl, wdw in [("12m", 252), ("36m", 756)]:
        rc = ce.pct_change(wdw).dropna(); rs = se.pct_change(wdw).dropna()
        j = rc.index.intersection(rs.index)
        beat = (rc[j].values > rs[j].values).mean() * 100
        neg = (rc[j].values < 0).mean() * 100
        print("rolling %s: combo>SPY en %.0f%% ventanas | combo negativo en %.0f%% | peor %s combo %+.1f%% vs SPY %+.1f%%"
              % (lbl, beat, neg, lbl, rc[j].min() * 100, rs[j].min() * 100))

    # ------------------------------------------------------------------ crisis
    print()
    print("=" * 78)
    print("4. CRISIS (retorno del tramo y peor drawdown dentro)")
    print("=" * 78)
    crisis = [("2018 Q4", "2018-10-01", "2018-12-31"), ("COVID crash", "2020-02-19", "2020-03-23"),
              ("2020 completo", "2020-01-01", "2020-12-31"), ("Bear 2022", "2022-01-01", "2022-12-31"),
              ("2025 hasta hoy", "2025-01-01", "2026-07-09")]
    print("%-16s  COMBO ret / dd      SPY ret / dd" % "tramo")
    for nm, a, b in crisis:
        msk = ((dates >= a) & (dates <= b)).values
        cdd = maxdd(np.where(msk, combo, np.nan)[msk]); sdd = maxdd(np.where(msk, spy, np.nan)[msk])
        print("%-16s %+7.1f%% / %5.1f%%   %+7.1f%% / %5.1f%%" % (nm, wret(combo, msk), cdd, wret(spy, msk), sdd))

    # ------------------------------------------------------------------ sub-periodos
    print()
    print("=" * 78)
    print("5. SUB-PERIODOS")
    print("=" * 78)
    for nm, a, b in [("2015-2019", 2015, 2019), ("2020-2022", 2020, 2022), ("2023-2026", 2023, 2026)]:
        msk = (yrs >= a) & (yrs <= b)
        rc = combo[msk & np.isfinite(combo)]; rs = spy[msk & np.isfinite(spy)]
        print("%-10s combo: CAGR %5.1f Sharpe %5.2f MaxDD %6.1f | SPY: CAGR %5.1f Sharpe %5.2f MaxDD %6.1f"
              % (nm, cagr(rc), sh(rc), maxdd(rc), cagr(rs), sh(rs), maxdd(rs)))

    # ------------------------------------------------------------------ sub-estrategias
    print()
    print("=" * 78)
    print("6. SUB-ESTRATEGIAS SOLAS vs COMBO (misma regla semanal+banda8, net 10bps)")
    print("=" * 78)
    print("%-22s  CAGR  Sharpe  MaxDD  Calmar" % "estrategia")
    for nm, key in [("S1 SPY-or-Cash", "1_SPY_or_Cash"), ("S2 Defense First", "2_DefenseFirst"),
                    ("S3 Blend 50/50", "4_Blend50_50"), ("(HAA puro)", "3_HAA")]:
        net, _, _ = sim(W[key][ASSETS].values, R, check)
        r = ratios(net)
        print("%-22s %5.1f  %5.2f  %6.1f  %5.2f" % (nm, r["CAGR"], r["Sharpe"], r["MaxDD"], r["Calmar"]))
    r = ratios(combo)
    print("%-22s %5.1f  %5.2f  %6.1f  %5.2f   <== COMBO" % ("CENTINELA (1/3 c/u)", r["CAGR"], r["Sharpe"], r["MaxDD"], r["Calmar"]))

    # ------------------------------------------------------------------ estres
    print()
    print("=" * 78)
    print("7. ESTRES DE EJECUCION")
    print("=" * 78)
    tgt_delay = np.vstack([np.full((1, 6), np.nan), tgt[:-1]])     # decision con 1 dia extra de retraso
    dl, _, _ = sim(tgt_delay, R, check)
    print("delay +1 dia:  CAGR %5.1f  Sharpe %.2f  MaxDD %6.1f   (base: %5.1f / %.2f / %6.1f)"
          % (cagr(dl), sh(dl[np.isfinite(dl)]), maxdd(dl), cagr(combo), sh(combo[np.isfinite(combo)]), maxdd(combo)))
    print("costes bps -> Sharpe: ", end="")
    for cb in [5, 10, 20, 30]:
        nt, _, _ = sim(tgt, R, check, 8.0, float(cb))
        print("%dbps %.2f  " % (cb, sh(nt[np.isfinite(nt)])), end="")
    print()
    dow = dates.dt.dayofweek.values
    print("dia rebalanceo -> Sharpe: ", end="")
    for k, nm in [(0, "Lun"), (1, "Mar"), (2, "Mie"), (3, "Jue"), (4, "Vie")]:
        nt, _, _ = sim(tgt, R, dow == k)
        print("%s %.2f  " % (nm, sh(nt[np.isfinite(nt)])), end="")
    print()

    # ------------------------------------------------------------------ por ano vs SPY
    print()
    print("=" * 78)
    print("8. POR ANO: combo vs SPY (neto)")
    print("=" * 78)
    wins = 0; tot = 0
    for y in sorted(set(yrs)):
        msk = (yrs == y)
        rc, rs = wret(combo, msk), wret(spy, msk)
        if np.isnan(rc):
            continue
        tot += 1; wins += 1 if rc > rs else 0
        print("  %d: combo %+6.1f%%  SPY %+6.1f%%  %s" % (y, rc, rs, "COMBO" if rc > rs else "spy"))
    print("  anos ganando a SPY: %d/%d" % (wins, tot))


if __name__ == "__main__":
    main()
