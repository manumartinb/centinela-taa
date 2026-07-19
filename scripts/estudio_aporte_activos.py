"""
estudio_aporte_activos.py - Generaliza el estudio "Aporte de DBC" a TODOS los
activos del combo CENTINELA: QQQ, SPY, SHV, TLT, DBC, GLD (+ canario TIP).

Para cada activo invertible, sobre los pesos EXACTOS de TradingView
(CBOE_DLY_SPX, 1D.csv) con la config canonica (semanal 1er dia ISO + banda 8%,
neto 10 bps, leakage-free):

  1. Buy & hold del activo solo (mult, CAGR, Sharpe, MaxDD).
  2. Cronometrado: CAGR del activo SOLO en los dias en que el combo lo tiene
     (peso mantenido > 1%), vs su CAGR incondicional.
  3. Estadisticas de peso mantenido (medio / mediana / maximo / % dias).
  4. Leave-one-out: combo CON vs SIN el activo, con sustituto canonico:
        TLT/DBC/GLD -> SHV (liquidez)     [variante: proporcional al resto defensivo]
        QQQ -> SPY ; SPY -> QQQ (el otro motor)   [variante: -> SHV]
        SHV -> cash al 0% (mismo peso, sin remunerar; mide el carry)
     Metricas CON vs SIN: CAGR, Sharpe, MaxDD, peor ano.
  5. Aporte por ano = retorno anual CON - retorno anual SIN (convencion canonica).

TIP (canario, NO invertible): ablacion de senal sobre la reconstruccion canonica
(apr_combo): RISK-ON = mom(SPY)>0 AND mom(TIP)>0  vs  solo mom(SPY)>0 (y canario
QQQ sin TIP). Nota: reconstruccion, no pesos exactos (la senal no se puede
re-ejecutar sobre el CSV propietario).

Outputs: consola + ANALISIS/OUTPUT/data/asset_study_summary.csv
         + repo charts/asset_contribution.png + repo data/asset_study_summary.csv
Solo ASCII. Deterministico (sin RNG).
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import backtest_taa as bt
from apr_combo import sim, ratios, cg, mom13612, ASSETS, BAND, COST

REPO = r"C:\Users\Administrator\Desktop\centinela-taa"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ANALISIS", "OUTPUT", "data")
COMP = ["2_DefenseFirst", "4_Blend50_50", "1_SPY_or_Cash"]
SUBST = {"TLT": "SHV", "DBC": "SHV", "GLD": "SHV", "QQQ": "SPY", "SPY": "QQQ"}
SUBST_VAR = {"TLT": "prop", "DBC": "prop", "GLD": "prop", "QQQ": "SHV", "SPY": "SHV"}
SUBST_TXT = {"TLT": "-> liquidez", "DBC": "-> liquidez", "GLD": "-> liquidez",
             "QQQ": "-> SPY", "SPY": "-> QQQ", "SHV": "-> cash 0%"}

SURF = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; GRID = "#e6e5e1"
BLUE = "#2a78d6"; GRAY = "#c9c7bf"
plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.axisbelow": True, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "font.size": 10,
    "axes.spines.top": False, "axes.spines.right": False})


def sim_path(tgt, R, check, band=BAND, cost=COST):
    """Identico a apr_combo.sim pero devuelve tambien la matriz de pesos
    mantenidos usados para el retorno de cada dia (rezagados/derivados)."""
    n = len(tgt); held = None; port = np.full(n, np.nan); turn = np.zeros(n)
    Wp = np.full((n, tgt.shape[1]), np.nan)
    for t in range(n):
        if held is not None and not np.isnan(R[t]).any():
            Wp[t] = held
            port[t] = np.nansum(held * R[t]); g = held * (1 + R[t]); held = g / g.sum()
        if check[t] and not np.isnan(tgt[t]).any():
            if held is None:
                held = tgt[t].copy()
            else:
                gap = np.nansum(np.abs(tgt[t] - held)) / 2.0
                if band <= 0 or gap > band / 100.0:
                    turn[t] = gap; held = tgt[t].copy()
    c = np.r_[0.0, turn[:-1]] * cost / 1e4
    return port - c, Wp


def yearly(net, yrs):
    return {int(y): (np.prod(1 + net[(yrs == y) & np.isfinite(net)]) - 1) * 100
            for y in sorted(set(yrs)) if ((yrs == y) & np.isfinite(net)).sum() > 20}


def reassign(tgt, asset, mode):
    """Devuelve tgt con el peso de `asset` reasignado segun `mode`
    ('prop' = proporcional al resto del menu defensivo; o un ticker destino)."""
    ia = ASSETS.index(asset)
    t2 = tgt.copy()
    if mode == "prop":
        men = [ASSETS.index(a) for a in ["SHV", "TLT", "DBC", "GLD"] if a != asset]
        ish = ASSETS.index("SHV")
        for t in range(len(t2)):
            w = t2[t, ia]
            if not np.isfinite(w):
                continue
            if w > 0:
                s = np.nansum(t2[t, men])
                if s > 1e-12:
                    for j in men:
                        t2[t, j] += w * t2[t, j] / s
                else:
                    t2[t, ish] += w
            t2[t, ia] = 0.0
    else:
        j = ASSETS.index(mode)
        w = t2[:, ia]
        t2[:, j] = t2[:, j] + np.where(np.isfinite(w), w, 0.0)
        t2[:, ia] = np.where(np.isfinite(w), 0.0, np.nan)
    return t2


def combo_target_ablate(m, M, use_tip=True, qcap=0.5, qtilt=1.0):
    """Copia de apr_combo.combo_target con opcion de ablacion del canario TIP."""
    n = len(m); tgt = np.full((n, 6), np.nan)
    for t in range(n):
        if any(np.isnan(M[a][t]) for a in M):
            continue
        if use_tip:
            rO = (M["SPY"][t] > 0 and M["TIP"][t] > 0)
            can = (M["TIP"][t] > 0 and M["QQQ"][t] > 0)
        else:
            rO = (M["SPY"][t] > 0)
            can = (M["QQQ"][t] > 0)
        pos = {a: max(0.0, M[a][t]) for a in ["SHV", "TLT", "DBC", "GLD"]}
        ds = sum(pos.values())
        dw = {a: (pos[a] / ds if ds > 0 else (1.0 if a == "SHV" else 0.0)) for a in pos}
        pq = max(0.0, M["QQQ"][t])
        qsh = (pq * qtilt) / (pq * qtilt + ds) if (pq * qtilt + ds) > 0 else 0.0
        qdef = min(qcap, qsh) if can else 0.0
        qbl = ((1.0 if can else 0.0) + qdef) / 2.0
        w = {a: 0.0 for a in ASSETS}
        w["SPY"] += 1.0 if rO else 0.0
        w["SHV"] += 0.0 if rO else 1.0
        w["QQQ"] += qdef + qbl
        for a in ["SHV", "TLT", "DBC", "GLD"]:
            w[a] += (1 - qdef) * dw[a] + (1 - qbl) * dw[a]
        for a in ASSETS:
            tgt[t, ASSETS.index(a)] = w[a] / 3.0
    return tgt


def main():
    os.makedirs(OUT, exist_ok=True)
    sig, p = bt.load()
    m = pd.merge(sig, p, on="date", how="inner").sort_values("date").reset_index(drop=True)
    W = bt.build_weights(m)
    tgt = sum(W[c][ASSETS].values for c in COMP) / 3.0
    R = m[["PX_" + a for a in ASSETS]].pct_change().values
    dates = m["date"]; yrs = dates.dt.year.values
    ic = dates.dt.isocalendar(); wk = ic.week.values + ic.year.values * 100
    check = np.r_[True, wk[1:] != wk[:-1]]

    netC, Wp = sim_path(tgt, R, check)
    netRef = sim(tgt, R, check)[0]
    assert np.allclose(np.nan_to_num(netC), np.nan_to_num(netRef)), "sim_path difiere de sim"
    ok = np.isfinite(netC)
    rC = ratios(netC); yC = yearly(netC, yrs)
    worstC = min(yC.values())
    print("=== ESTUDIO DE APORTE POR ACTIVO (pesos EXACTOS TradingView) ===")
    print("Ventana %s..%s | N=%d dias | semanal+banda %.0f%% | neto %.0f bps"
          % (dates[ok].min().date(), dates.max().date(), ok.sum(), BAND, COST))
    print("COMBO: CAGR %.2f | Sharpe %.3f | MaxDD %.2f | peor ano %.1f\n"
          % (rC["CAGR"], rC["Sharpe"], rC["MaxDD"], worstC))

    rows = []; aportes = {}
    for a in ASSETS:
        ia = ASSETS.index(a)
        ra = R[ok, ia]
        bh = ratios(ra); mult = float(np.prod(1 + ra[np.isfinite(ra)]))
        wA = Wp[:, ia]
        heldmsk = ok & (wA > 0.01)
        timed = cg(R[heldmsk, ia]) if heldmsk.sum() > 60 else np.nan
        wall = wA[ok]
        wheld = wA[heldmsk]
        pdays = 100.0 * heldmsk.sum() / ok.sum()
        contrib = np.where(np.isfinite(wA) & np.isfinite(R[:, ia]), wA * R[:, ia], np.nan)
        cyr = {int(y): np.nansum(contrib[(yrs == y)]) * 100 for y in yC}

        if a == "SHV":
            Rm = R.copy()
            Rm[:, ia] = np.where(np.isfinite(R[:, ia]), 0.0, R[:, ia])
            netS = sim(tgt, Rm, check)[0]
            netV = None
        else:
            netS = sim(reassign(tgt, a, SUBST[a]), R, check)[0]
            netV = sim(reassign(tgt, a, SUBST_VAR[a]), R, check)[0]
        rS = ratios(netS); yS = yearly(netS, yrs)
        worstS = min(yS.values())
        ap = {y: yC[y] - yS.get(y, np.nan) for y in yC}
        aportes[a] = ap
        rV = ratios(netV) if netV is not None else None

        print("--- %s (sustituto SIN: %s) ---" % (a, SUBST_TXT[a]))
        print("  B&H solo:        x%.2f | CAGR %5.2f | Sharpe %5.2f | MaxDD %6.1f"
              % (mult, bh["CAGR"], bh["Sharpe"], bh["MaxDD"]))
        print("  Cronometrado:    CAGR %5.2f (dias en cartera: %.1f%%)" % (timed, pdays))
        print("  Peso mantenido:  medio %.1f%% | mediana %.1f%% | max %.1f%% (sobre todos los dias)"
              % (100 * np.nanmean(wall), 100 * np.nanmedian(wall), 100 * np.nanmax(wall)))
        print("                   medio %.1f%% | mediana %.1f%% (solo dias en cartera)"
              % (100 * np.nanmean(wheld), 100 * np.nanmedian(wheld)))
        print("  COMBO CON:       CAGR %5.2f | Sharpe %5.3f | MaxDD %6.2f | peor ano %5.1f"
              % (rC["CAGR"], rC["Sharpe"], rC["MaxDD"], worstC))
        print("  COMBO SIN:       CAGR %5.2f | Sharpe %5.3f | MaxDD %6.2f | peor ano %5.1f"
              % (rS["CAGR"], rS["Sharpe"], rS["MaxDD"], worstS))
        if rV is not None:
            print("  SIN (variante %s): CAGR %5.2f | Sharpe %5.3f | MaxDD %6.2f"
                  % (SUBST_VAR[a], rV["CAGR"], rV["Sharpe"], rV["MaxDD"]))
        print("  Aporte por ano (CON-SIN, pp):",
              {y: round(v, 1) for y, v in ap.items()})
        print("  Contrib. directa por ano (w*r, pp):",
              {y: round(v, 1) for y, v in cyr.items()})
        print()
        rows.append(dict(asset=a, subst=SUBST_TXT[a],
                         bh_mult=round(mult, 2), bh_cagr=round(bh["CAGR"], 2),
                         bh_sharpe=round(bh["Sharpe"], 2), bh_maxdd=round(bh["MaxDD"], 1),
                         timed_cagr=round(timed, 2), pct_days_held=round(pdays, 1),
                         w_mean=round(100 * np.nanmean(wall), 1),
                         w_median=round(100 * np.nanmedian(wall), 1),
                         w_max=round(100 * np.nanmax(wall), 1),
                         sin_cagr=round(rS["CAGR"], 2), sin_sharpe=round(rS["Sharpe"], 3),
                         sin_maxdd=round(rS["MaxDD"], 2), sin_worst_year=round(worstS, 1),
                         d_cagr=round(rC["CAGR"] - rS["CAGR"], 2),
                         d_sharpe=round(rC["Sharpe"] - rS["Sharpe"], 3),
                         d_worst_year=round(worstC - worstS, 1),
                         var_cagr=(round(rV["CAGR"], 2) if rV is not None else np.nan),
                         var_sharpe=(round(rV["Sharpe"], 3) if rV is not None else np.nan)))

    # ---- TIP (canario): ablacion sobre la reconstruccion ----
    M = {a: mom13612(m["PX_" + a]) for a in ["QQQ", "SHV", "TLT", "DBC", "GLD", "SPY", "TIP"]}
    tgtT = combo_target_ablate(m, M, use_tip=True)
    tgtN = combo_target_ablate(m, M, use_tip=False)
    netT = sim(tgtT, R, check)[0]; netN = sim(tgtN, R, check)[0]
    rT = ratios(netT); rN = ratios(netN)
    yT = yearly(netT, yrs); yN = yearly(netN, yrs)
    apT = {y: round(yT[y] - yN.get(y, np.nan), 1) for y in yT}
    print("--- TIP (canario de regimen; ablacion de SENAL, reconstruccion canonica) ---")
    print("  CON TIP: CAGR %5.2f | Sharpe %5.3f | MaxDD %6.2f | peor ano %5.1f"
          % (rT["CAGR"], rT["Sharpe"], rT["MaxDD"], min(yT.values())))
    print("  SIN TIP: CAGR %5.2f | Sharpe %5.3f | MaxDD %6.2f | peor ano %5.1f"
          % (rN["CAGR"], rN["Sharpe"], rN["MaxDD"], min(yN.values())))
    print("  Aporte por ano (pp):", apT)
    rows.append(dict(asset="TIP (senal)", subst="regimen sin canario",
                     bh_mult=np.nan, bh_cagr=np.nan, bh_sharpe=np.nan, bh_maxdd=np.nan,
                     timed_cagr=np.nan, pct_days_held=0.0, w_mean=0.0, w_median=0.0, w_max=0.0,
                     sin_cagr=round(rN["CAGR"], 2), sin_sharpe=round(rN["Sharpe"], 3),
                     sin_maxdd=round(rN["MaxDD"], 2), sin_worst_year=round(min(yN.values()), 1),
                     d_cagr=round(rT["CAGR"] - rN["CAGR"], 2),
                     d_sharpe=round(rT["Sharpe"] - rN["Sharpe"], 3),
                     d_worst_year=round(min(yT.values()) - min(yN.values()), 1),
                     var_cagr=np.nan, var_sharpe=np.nan))

    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "asset_study_summary.csv"), index=False)
    df.to_csv(os.path.join(REPO, "data", "asset_study_summary.csv"), index=False)
    print("\nCSV ->", os.path.join(OUT, "asset_study_summary.csv"), "y repo/data/")

    # ---- chart: 6 paneles de aporte por ano ----
    fig, axes = plt.subplots(2, 3, figsize=(11.5, 6.8), sharex=True)
    order = ["QQQ", "SPY", "SHV", "TLT", "DBC", "GLD"]
    ylist = sorted(yC)
    for k, a in enumerate(order):
        ax = axes[k // 3][k % 3]
        vals = [aportes[a].get(y, np.nan) for y in ylist]
        cols = [BLUE if (np.isfinite(v) and v >= 0) else GRAY for v in vals]
        ax.bar(range(len(ylist)), vals, 0.65, color=cols)
        ax.axhline(0, color=INK2, lw=0.8)
        dC = [r for r in rows if r["asset"] == a][0]["d_cagr"]
        ax.set_title("%s  (sin el: %s)   dCAGR %+.1f pp" % (a, SUBST_TXT[a], dC),
                     loc="left", fontsize=10.5, fontweight="bold")
        vmin = min(0.0, np.nanmin(vals)); vmax = max(0.0, np.nanmax(vals))
        ax.set_ylim(vmin * 1.22 - 0.3, vmax * 1.22 + 0.3)
        for i, v in enumerate(vals):
            if np.isfinite(v) and abs(v) >= 1.5:
                ax.annotate("%+.1f" % v, (i, v + (0.15 if v >= 0 else -0.55)),
                            ha="center", fontsize=8, fontweight="bold",
                            color=BLUE if v >= 0 else INK2)
        ax.set_xticks(range(len(ylist)))
        ax.set_xticklabels(["'%02d" % (y % 100) for y in ylist], fontsize=8)
    fig.suptitle("Aporte de cada activo al combo, por ano (pp de retorno: CON menos SIN)",
                 x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(os.path.join(REPO, "charts", "asset_contribution.png"),
                dpi=150, bbox_inches="tight", facecolor=SURF)
    plt.close(fig)
    print("chart -> repo charts/asset_contribution.png")


if __name__ == "__main__":
    main()
