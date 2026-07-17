"""
apr_combo.py - APR (Analisis de Predictabilidad y Robustez) del TAA Combo.

RECONSTRUCCION: el CSV exacto de TradingView (CBOE_DLY_SPX, 1D.csv) NO existe hoy,
asi que este script reconstruye el combo desde el momentum de los precios ETF cacheados.
Regimen y momentum son EXACTOS vs ese CSV cuando existia (error 0.000 / match 100%);
el sizing fraccional de Defense First es aproximado (corr diaria ~0.85 vs exacto).

Combo = mean(Defense First, Blend 50/50, SPY-or-Cash). Chequeo semanal (primer dia ISO)
+ banda de deriva 8%. Leakage-free (peso rezagado 1 dia). Coste 10 bps/turnover. rf=0.
Corrige el APR previo: el null de timing es AHORA diario leakage-free (el semanal
tenia look-ahead de 1 dia y su p variaba 0.004-0.11 segun alineacion). Solo ASCII.
"""
import os
import numpy as np
import pandas as pd

SEED = 42
BAND = 8.0     # umbral de deriva (%)
COST = 10.0    # bps por unidad de turnover
BASE = os.path.dirname(os.path.abspath(__file__))
ETF = os.path.join(BASE, "ANALISIS", "OUTPUT", "data", "etf_adjclose.csv")
ASSETS = ["QQQ", "SHV", "TLT", "DBC", "GLD", "SPY"]


def mom13612(px):
    p = px.values.astype(float); n = len(p); o = np.full(n, np.nan)
    for t in range(252, n):
        o[t] = (12*(p[t]/p[t-21]-1) + 4*(p[t]/p[t-63]-1) + 2*(p[t]/p[t-126]-1) + 1*(p[t]/p[t-252]-1)) / 4.0
    return o


def combo_target(m, M, qcap=0.5, qtilt=1.0):
    n = len(m); tgt = np.full((n, 6), np.nan)
    for t in range(n):
        if any(np.isnan(M[a][t]) for a in M):
            continue
        rO = (M["SPY"][t] > 0 and M["TIP"][t] > 0)
        can = (M["TIP"][t] > 0 and M["QQQ"][t] > 0)
        pos = {a: max(0.0, M[a][t]) for a in ["SHV", "TLT", "DBC", "GLD"]}
        ds = sum(pos.values())
        dw = {a: (pos[a]/ds if ds > 0 else (1.0 if a == "SHV" else 0.0)) for a in pos}
        pq = max(0.0, M["QQQ"][t])
        qsh = (pq*qtilt) / (pq*qtilt + ds) if (pq*qtilt + ds) > 0 else 0.0
        qdef = min(qcap, qsh) if can else 0.0
        qbl = ((1.0 if can else 0.0) + qdef) / 2.0
        w = {a: 0.0 for a in ASSETS}
        w["SPY"] += 1.0 if rO else 0.0
        w["SHV"] += 0.0 if rO else 1.0
        w["QQQ"] += qdef + qbl
        for a in ["SHV", "TLT", "DBC", "GLD"]:
            w[a] += (1 - qdef)*dw[a] + (1 - qbl)*dw[a]
        for a in ASSETS:
            tgt[t, ASSETS.index(a)] = w[a] / 3.0
    return tgt


def sim(tgt, R, check, band=BAND, cost=COST):
    """Backtest diario leakage-free: deriva de pesos + rebalanceo con banda el dia de chequeo."""
    n = len(tgt); held = None; port = np.full(n, np.nan); turn = np.zeros(n); nreb = 0
    for t in range(n):
        if held is not None and not np.isnan(R[t]).any():
            port[t] = np.nansum(held*R[t]); g = held*(1+R[t]); held = g/g.sum()
        if check[t] and not np.isnan(tgt[t]).any():
            if held is None:
                held = tgt[t].copy(); nreb += 1
            else:
                gap = np.nansum(np.abs(tgt[t]-held)) / 2.0
                if band <= 0 or gap > band/100.0:
                    turn[t] = gap; held = tgt[t].copy(); nreb += 1
    c = np.r_[0.0, turn[:-1]]*cost/1e4
    fin = np.isfinite(port).sum()
    return port - c, np.nansum(turn)/(fin/252.0), nreb/(fin/252.0)


def ratios(r):
    r = r[np.isfinite(r)]; eq = np.cumprod(1+r); y = len(r)/252.0
    dd = (eq/np.maximum.accumulate(eq) - 1); dn = r[r < 0].std(ddof=1)*np.sqrt(252)
    cg = eq[-1]**(1/y) - 1
    return dict(CAGR=cg*100, Sharpe=r.mean()/r.std(ddof=1)*np.sqrt(252), Sortino=(r.mean()*252)/dn,
                Calmar=cg/abs(dd.min()), MaxDD=dd.min()*100, Vol=r.std(ddof=1)*np.sqrt(252)*100)


def sh(x):
    x = x[np.isfinite(x)]
    return x.mean()/x.std(ddof=1)*np.sqrt(252)


def cg(x):
    x = x[np.isfinite(x)]; e = np.cumprod(1+x)
    return (e[-1]**(252/len(x)) - 1)*100


def main():
    np.random.seed(SEED)
    m = pd.read_csv(ETF); m["date"] = pd.to_datetime(m["date"])
    m = m.sort_values("date").reset_index(drop=True)
    M = {a: mom13612(m[a]) for a in ["QQQ", "SHV", "TLT", "DBC", "GLD", "SPY", "TIP"]}
    tgt = combo_target(m, M)
    R = m[ASSETS].pct_change().values
    yrs = m["date"].dt.year.values
    oos = (m["date"] >= "2025-01-01").values
    ic = m["date"].dt.isocalendar(); wk = ic.week.values + ic.year.values*100
    check = np.r_[True, wk[1:] != wk[:-1]]                 # primer dia de cada semana ISO

    net, tn, nr = sim(tgt, R, check)
    r0 = ratios(net)
    print("=== APR TAA COMBO (reconstruido; CSV exacto TradingView AUSENTE) ===")
    print("Ventana %s..%s | N=%d | semanal primer dia ISO + banda %.0f%% | net %.0f bps | turnover %.3fx | reb/ano %.3f"
          % (m["date"][np.isfinite(net)].min().date(), m["date"].max().date(),
             np.isfinite(net).sum(), BAND, COST, tn, nr))
    for k, v in r0.items():
        print("  %-7s %.6f" % (k, v))
    print("  IS(<=2024) CAGR %.4f Sharpe %.6f | OOS(>=2025) CAGR %.4f Sharpe %.6f"
          % (cg(net[~oos]), sh(net[~oos]), cg(net[oos]), sh(net[oos])))
    print("  por ano:", {int(y): round((np.prod(1+net[(yrs == y) & np.isfinite(net)])-1)*100, 1)
                          for y in sorted(set(yrs)) if ((yrs == y) & np.isfinite(net)).sum() > 20})

    rr = net[np.isfinite(net)]; NB = 2000
    iid = np.array([sh(rr[np.random.randint(0, len(rr), len(rr))]) for _ in range(NB)])
    mon = (m["date"].dt.year*12 + m["date"].dt.month).values[np.isfinite(net)]
    blk = [rr[mon == u] for u in np.unique(mon)]
    bb = np.array([sh(np.concatenate([blk[i] for i in np.random.randint(0, len(blk), len(blk))])) for _ in range(NB)])
    print("  bootstrap Sharpe CI95 iid [%.4f, %.4f] | bloque-mes [%.4f, %.4f]"
          % (np.percentile(iid, 2.5), np.percentile(iid, 97.5), np.percentile(bb, 2.5), np.percentile(bb, 97.5)))

    # NULL DE TIMING DIARIO leakage-free: peso de la semana rezagado 1 dia; permutar semanas
    wids = [u for u in np.unique(wk) if np.isfinite(tgt[np.where(wk == u)[0][0], 0])]
    wkix = {u: i for i, u in enumerate(wids)}
    Tw = np.array([tgt[np.where(wk == u)[0][0]] for u in wids])
    dayw = np.array([wkix.get(wk[t], -1) for t in range(len(m))])

    def null_sharpe(assign):
        Td = np.full((len(m), 6), np.nan); ok = dayw >= 0
        Td[ok] = Tw[assign[dayw[ok]]]
        wl = np.roll(Td, 1, axis=0); wl[0] = np.nan
        rd = np.nansum(wl*R, axis=1); mk = np.isfinite(rd) & (dayw > 0)
        return rd[mk].mean()/rd[mk].std(ddof=1)*np.sqrt(252)

    real = null_sharpe(np.arange(len(wids)))
    nul = np.array([null_sharpe(np.random.permutation(len(wids))) for _ in range(NB)])
    print("  NULL timing diario leakage-free: Sharpe real %.4f | null %.4f +- %.4f | p(null>=real)=%.4f"
          % (real, nul.mean(), nul.std(), (nul >= real).mean()))

    print("  sens banda 5/8/12%%: %.4f / %.4f / %.4f | coste 5/10/20 bps: %.4f / %.4f / %.4f"
          % (ratios(sim(tgt, R, check, 5)[0])["Sharpe"], r0["Sharpe"], ratios(sim(tgt, R, check, 12)[0])["Sharpe"],
             ratios(sim(tgt, R, check, 8, 5)[0])["Sharpe"], r0["Sharpe"], ratios(sim(tgt, R, check, 8, 20)[0])["Sharpe"]))


if __name__ == "__main__":
    main()
