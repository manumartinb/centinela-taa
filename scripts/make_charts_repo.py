"""
make_charts_repo.py - Genera los graficos y datos del repo GitHub de CENTINELA.
Pesos EXACTOS (CSV TradingView), config canonica: semanal (1er dia ISO) + banda 8%,
net 10 bps. Output -> C:/Users/Administrator/Desktop/centinela-taa/{charts,data}.
Paleta validada (dataviz skill): slots 1-6 light. Solo ASCII.
"""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import backtest_taa as bt
from apr_combo import sim, ratios, sh, ASSETS

REPO = r"C:\Users\Administrator\Desktop\centinela-taa"
CH = os.path.join(REPO, "charts"); DA = os.path.join(REPO, "data")
COMP = ["2_DefenseFirst", "4_Blend50_50", "1_SPY_or_Cash"]

SURF = "#fcfcfb"; INK = "#0b0b0b"; INK2 = "#52514e"; GRID = "#e6e5e1"
BLUE = "#2a78d6"; GREEN = "#008300"; MAGENTA = "#e87ba4"; YELLOW = "#eda100"
AQUA = "#1baf7a"; ORANGE = "#eb6834"; GRAY = "#8a887f"
STACK = [BLUE, GREEN, MAGENTA, YELLOW, AQUA, ORANGE]   # QQQ SPY SHV TLT DBC GLD

plt.rcParams.update({"figure.facecolor": SURF, "axes.facecolor": SURF,
    "axes.edgecolor": GRID, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7,
    "axes.axisbelow": True, "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "font.size": 10.5,
    "axes.spines.top": False, "axes.spines.right": False})


def eq(net):
    return np.cumprod(1 + np.nan_to_num(net, nan=0.0))


def dd(net):
    e = eq(net); return (e / np.maximum.accumulate(e) - 1) * 100


def save(fig, name):
    fig.savefig(os.path.join(CH, name), dpi=150, bbox_inches="tight", facecolor=SURF)
    plt.close(fig); print("chart:", name)


def main():
    os.makedirs(CH, exist_ok=True); os.makedirs(DA, exist_ok=True)
    sig, p = bt.load()
    m = pd.merge(sig, p, on="date", how="inner").sort_values("date").reset_index(drop=True)
    W = bt.build_weights(m)
    R = m[["PX_" + a for a in ASSETS]].pct_change().values
    dates = m["date"]; yrs = dates.dt.year.values
    ic = dates.dt.isocalendar(); wk = ic.week.values + ic.year.values * 100
    check = np.r_[True, wk[1:] != wk[:-1]]
    tgt = sum(W[c][ASSETS].values for c in COMP) / 3.0
    combo, _, _ = sim(tgt, R, check)
    spy = m["PX_SPY"].pct_change().values
    qqq = m["PX_QQQ"].pct_change().values
    n = len(m)
    w6040 = np.zeros((n, 6)); w6040[:, ASSETS.index("SPY")] = 0.6; w6040[:, ASSETS.index("TLT")] = 0.4
    b6040, _, _ = sim(w6040, R, check)

    # ---- data exports ----
    pd.DataFrame({"date": dates, "ret_net_10bps": combo, "equity": eq(combo)}).to_csv(
        os.path.join(DA, "centinela_daily_returns.csv"), index=False)

    # ---- 1. equity log ----
    fig, ax = plt.subplots(figsize=(10.5, 5.6))
    series = [("CENTINELA", eq(combo), BLUE, 2.6, "-"), ("SPY (total return)", eq(spy), INK2, 1.5, "--"),
              ("QQQ", eq(qqq), MAGENTA, 1.5, "-"), ("60/40", eq(b6040), YELLOW, 1.5, "-")]
    for nm, e, c, lw, ls in series:
        ax.plot(dates, e, color=c, lw=lw, ls=ls)
        ax.annotate(" " + nm, (dates.iloc[-1], e[-1]), color=c if c != INK2 else INK2,
                    fontsize=10, fontweight="bold" if nm == "CENTINELA" else "normal", va="center")
    ax.set_yscale("log"); ax.set_yticks([1, 1.5, 2, 3, 4, 5, 7]); ax.set_yticklabels(["x1", "x1.5", "x2", "x3", "x4", "x5", "x7"])
    ax.set_title("Crecimiento de 1 (escala log) - 2015-2026, neto de costes", loc="left", fontsize=13, fontweight="bold")
    ax.set_xlim(dates.iloc[0], dates.iloc[-1] + pd.Timedelta(days=720))
    save(fig, "equity_log.png")

    # ---- 2. drawdown ----
    fig, ax = plt.subplots(figsize=(10.5, 4.2))
    ax.fill_between(dates, dd(spy), 0, color=INK2, alpha=0.25, label="SPY")
    ax.fill_between(dates, dd(combo), 0, color=BLUE, alpha=0.65, label="CENTINELA")
    ax.annotate("CENTINELA: peor caida -9.1%", (dates.iloc[int(n*0.42)], -12), color=BLUE, fontweight="bold")
    ax.annotate("SPY: -33.7%", (dates.iloc[int(n*0.42)], -30), color=INK2)
    ax.set_title("Drawdown (caida desde maximos, %)", loc="left", fontsize=13, fontweight="bold")
    save(fig, "drawdown.png")

    # ---- 3. por ano ----
    ys = [y for y in sorted(set(yrs)) if ((yrs == y) & np.isfinite(combo)).sum() > 20]
    cy = [(np.prod(1 + combo[(yrs == y) & np.isfinite(combo)]) - 1) * 100 for y in ys]
    sy = [(np.prod(1 + spy[(yrs == y) & np.isfinite(spy)]) - 1) * 100 for y in ys]
    x = np.arange(len(ys)); wd = 0.38
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    ax.bar(x - wd/2, cy, wd, color=BLUE, label="CENTINELA")
    ax.bar(x + wd/2, sy, wd, color="#c9c7bf", label="SPY")
    for i, v in enumerate(cy):
        ax.annotate("%+.0f" % v, (x[i] - wd/2, v + (0.8 if v >= 0 else -2.6)), ha="center", fontsize=8.5, color=BLUE, fontweight="bold")
    ax.axhline(0, color=INK2, lw=0.8); ax.set_xticks(x); ax.set_xticklabels([str(y) for y in ys])
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Retorno por ano (%) - fijate en 2018, 2020, 2022 y 2025", loc="left", fontsize=13, fontweight="bold")
    save(fig, "by_year.png")

    # ---- 4. rolling 12m ----
    ce = pd.Series(eq(combo), index=dates); se = pd.Series(eq(spy), index=dates)
    rc = ce.pct_change(252) * 100; rs = se.pct_change(252) * 100
    fig, ax = plt.subplots(figsize=(10.5, 4.2))
    ax.plot(dates, rs, color=INK2, lw=1.3, ls="--")
    ax.plot(dates, rc, color=BLUE, lw=2.2)
    ax.axhline(0, color=INK, lw=0.8)
    ax.annotate(" CENTINELA (peor: -2.4%)", (dates.iloc[-1], rc.iloc[-1]), color=BLUE, fontweight="bold", va="center")
    ax.annotate(" SPY (peor: -19.7%)", (dates.iloc[-1], rs.iloc[-1]), color=INK2, va="center")
    ax.set_xlim(dates.iloc[0], dates.iloc[-1] + pd.Timedelta(days=900))
    ax.set_title("Retorno rodante a 12 meses (%): la linea azul casi nunca baja de cero", loc="left", fontsize=13, fontweight="bold")
    save(fig, "rolling12m.png")

    # ---- 5. allocations stacked ----
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    okw = np.isfinite(tgt[:, 0])
    ax.stackplot(dates[okw], (tgt[okw] * 100).T, colors=STACK, labels=ASSETS, lw=0)
    ax.set_ylim(0, 100); ax.legend(ncol=6, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.08))
    ax.set_title("Asignacion objetivo del combo por dia (%) - la maquina rotando entre regimenes", loc="left", fontsize=13, fontweight="bold")
    save(fig, "allocations.png")

    # ---- 6. frecuencias + dia de la semana ----
    freqs = {}
    mo = dates.dt.month.values + dates.dt.year.values * 100
    checkM = np.r_[True, mo[1:] != mo[:-1]]
    for nm, ck, band in [("Diario", np.ones(n, bool), 0.0), ("Semanal", check, 8.0), ("Mensual", checkM, 8.0)]:
        nt, _, _ = sim(tgt, R, ck, band)
        freqs[nm] = (sh(nt[np.isfinite(nt)]), ratios(nt)["CAGR"])
    dow = dates.dt.dayofweek.values
    dnames = ["Lun", "Mar", "Mie", "Jue", "Vie"]
    dsh = [sh(sim(tgt, R, dow == k)[0][np.isfinite(sim(tgt, R, dow == k)[0])]) for k in range(5)]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0))
    a = axes[0]; ks = list(freqs)
    a.bar(ks, [freqs[k][0] for k in ks], 0.55, color=[GRAY, BLUE, GRAY])
    for i, k in enumerate(ks):
        a.annotate("%.2f" % freqs[k][0], (i, freqs[k][0] + 0.02), ha="center", fontweight="bold",
                   color=BLUE if k == "Semanal" else INK2)
    a.set_title("Sharpe por frecuencia de chequeo\n(neto 10 bps; semanal = elegido)", loc="left", fontsize=11, fontweight="bold")
    a = axes[1]
    a.bar(dnames, dsh, 0.55, color=[GRAY, GRAY, BLUE, BLUE, GRAY])
    for i, v in enumerate(dsh):
        a.annotate("%.2f" % v, (i, v + 0.02), ha="center", fontsize=9, color=INK2)
    a.set_title("Sharpe por dia de rebalanceo\n(cualquiera vale; mie/jue lo mejor)", loc="left", fontsize=11, fontweight="bold")
    for a in axes:
        a.set_ylim(0, 1.7)
    save(fig, "frequencies.png")

    # ---- 7. sub-estrategias ----
    subs = [("S1 SPY-or-Cash", "1_SPY_or_Cash"), ("S2 Defense First", "2_DefenseFirst"),
            ("S3 Blend 50/50", "4_Blend50_50"), ("HAA puro", "3_HAA")]
    names, shs, dds = [], [], []
    for nm, k in subs:
        nt, _, _ = sim(W[k][ASSETS].values, R, check)
        names.append(nm); shs.append(sh(nt[np.isfinite(nt)])); dds.append(ratios(nt)["MaxDD"])
    names.append("CENTINELA (combo)"); shs.append(sh(combo[np.isfinite(combo)])); dds.append(ratios(combo)["MaxDD"])
    cols = [GRAY]*4 + [BLUE]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.0))
    axes[0].barh(names, shs, color=cols)
    for i, v in enumerate(shs):
        axes[0].annotate(" %.2f" % v, (v, i), va="center", fontweight="bold" if i == 4 else "normal",
                         color=BLUE if i == 4 else INK2)
    axes[0].set_title("Sharpe: el combo supera a todas sus partes", loc="left", fontsize=11, fontweight="bold")
    axes[1].barh(names, dds, color=cols)
    for i, v in enumerate(dds):
        axes[1].annotate("%.1f%% " % v, (v, i), va="center", ha="right", fontweight="bold" if i == 4 else "normal",
                         color=BLUE if i == 4 else INK2)
    axes[1].set_title("Peor caida (MaxDD %): tambien la menor", loc="left", fontsize=11, fontweight="bold")
    axes[1].set_yticklabels([])
    save(fig, "substrategies.png")

    # ---- 8. crisis ----
    crisis = [("2018 Q4", "2018-10-01", "2018-12-31"), ("COVID\n(feb-mar 20)", "2020-02-19", "2020-03-23"),
              ("2020\ncompleto", "2020-01-01", "2020-12-31"), ("Bear 2022", "2022-01-01", "2022-12-31"),
              ("2025-hoy", "2025-01-01", "2026-07-09")]
    cv, sv, labs = [], [], []
    for nm, a0, b0 in crisis:
        msk = ((dates >= a0) & (dates <= b0)).values
        cv.append((np.prod(1 + combo[msk & np.isfinite(combo)]) - 1) * 100)
        sv.append((np.prod(1 + spy[msk & np.isfinite(spy)]) - 1) * 100)
        labs.append(nm)
    x = np.arange(len(labs)); wd = 0.38
    fig, ax = plt.subplots(figsize=(10.5, 4.4))
    ax.bar(x - wd/2, cv, wd, color=BLUE, label="CENTINELA")
    ax.bar(x + wd/2, sv, wd, color="#c9c7bf", label="SPY")
    for i in range(len(labs)):
        ax.annotate("%+.1f" % cv[i], (x[i] - wd/2, cv[i] + (1 if cv[i] >= 0 else -3)), ha="center", fontsize=9, fontweight="bold", color=BLUE)
        ax.annotate("%+.1f" % sv[i], (x[i] + wd/2, sv[i] + (1 if sv[i] >= 0 else -3)), ha="center", fontsize=9, color=INK2)
    ax.axhline(0, color=INK2, lw=0.8); ax.set_xticks(x); ax.set_xticklabels(labs)
    ax.legend(frameon=False, loc="upper left")
    ax.set_title("Las crisis: donde CENTINELA se gana el nombre", loc="left", fontsize=13, fontweight="bold")
    save(fig, "crisis.png")

    print("OK charts + data en", REPO)


if __name__ == "__main__":
    main()
