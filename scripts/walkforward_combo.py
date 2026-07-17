"""
walkforward_combo.py - Anti-overfitting del TAA Combo CENTINELA.
(A) Walk-forward EXACTO: banda re-seleccionada cada ano con SOLO datos pasados,
    evaluada OOS -> prueba que la eleccion de banda no esta sobreajustada.
(B) Perturbacion de los pesos del combo (1/3,1/3,1/3 +/- 20%) sobre el EXACTO.
(C) Perturbacion de los lookbacks del momentum (+/- 20%) sobre la RECONSTRUCCION.
Solo ASCII.
"""
import numpy as np
import pandas as pd
import backtest_taa as bt
from apr_combo import sim, ratios, sh, ASSETS, mom13612

COMP = ["2_DefenseFirst", "4_Blend50_50", "1_SPY_or_Cash"]


def yret(net, yrs, Y):
    m = (yrs == Y) & np.isfinite(net)
    return (np.prod(1 + net[m]) - 1) * 100 if m.sum() > 5 else np.nan


def main():
    np.random.seed(42)
    sig, p = bt.load()
    m = pd.merge(sig, p, on="date", how="inner").sort_values("date").reset_index(drop=True)
    W = bt.build_weights(m)
    R = m[["PX_" + a for a in ASSETS]].pct_change().values
    yrs = m["date"].dt.year.values
    ic = m["date"].dt.isocalendar(); wk = ic.week.values + ic.year.values * 100
    check = np.r_[True, wk[1:] != wk[:-1]]
    tgt = sum(W[c][ASSETS].values for c in COMP) / 3.0

    # ---------- (A) Walk-forward: banda re-seleccionada con datos pasados ----------
    bands = [0, 5, 8, 10, 12, 15]
    nets = {b: sim(tgt, R, check, b)[0] for b in bands}
    years = sorted(set(yrs))
    test_years = [y for y in years if y >= 2018]   # >=3 anos de train
    print("=== (A) WALK-FORWARD banda re-seleccionada (EXACTO, semanal, net 10bps) ===")
    print("test  banda_elegida(train)  OOS_ret%(reselec)  OOS_ret%(fijo8%)")
    oos_re, oos_8 = [], []
    for Y in test_years:
        tr = (yrs < Y)
        best_b = max(bands, key=lambda b: sh(nets[b][tr & np.isfinite(nets[b])]))
        print("%d        %2d%%                %+6.1f            %+6.1f"
              % (Y, best_b, yret(nets[best_b], yrs, Y), yret(nets[8], yrs, Y)))
        te = (yrs == Y)
        oos_re.append(nets[best_b][te & np.isfinite(nets[best_b])])
        oos_8.append(nets[8][te & np.isfinite(nets[8])])
    ore = np.concatenate(oos_re); o8 = np.concatenate(oos_8)
    print("AGREGADO OOS (%d anos): reselec Sharpe %.2f  CAGR %.1f%%  |  fijo8%% Sharpe %.2f  CAGR %.1f%%"
          % (len(test_years), sh(ore), (np.prod(1+ore)**(252/len(ore))-1)*100,
             sh(o8), (np.prod(1+o8)**(252/len(o8))-1)*100))

    # ---------- (B) Perturbacion de pesos del combo (EXACTO) ----------
    print()
    print("=== (B) PERTURBACION pesos combo (S1 SPYCash / S2 DefFirst / S3 Blend) ===")
    mixes = [("1/3-1/3-1/3 (base)", [1/3, 1/3, 1/3]),
             ("0.40/0.30/0.30", [0.40, 0.30, 0.30]),
             ("0.30/0.40/0.30", [0.30, 0.40, 0.30]),
             ("0.30/0.30/0.40", [0.30, 0.30, 0.40]),
             ("0.20/0.40/0.40", [0.20, 0.40, 0.40]),
             ("0.50/0.25/0.25", [0.50, 0.25, 0.25])]
    Wl = {"S1": W["1_SPY_or_Cash"][ASSETS].values, "S2": W["2_DefenseFirst"][ASSETS].values, "S3": W["4_Blend50_50"][ASSETS].values}
    print("mezcla                CAGR  Sharpe  MaxDD")
    for nm, (a, b, c) in mixes:
        tg = a*Wl["S1"] + b*Wl["S2"] + c*Wl["S3"]
        r = ratios(sim(tg, R, check, 8)[0])
        print("%-20s  %5.1f  %.2f  %6.1f" % (nm, r["CAGR"], r["Sharpe"], r["MaxDD"]))

    # ---------- (C) Perturbacion lookbacks momentum (RECONSTRUCCION) ----------
    print()
    print("=== (C) PERTURBACION lookbacks momentum +/-20% (RECONSTRUCCION) ===")
    etf = pd.read_csv("ANALISIS/OUTPUT/data/etf_adjclose.csv"); etf["date"] = pd.to_datetime(etf["date"])
    e = etf.sort_values("date").reset_index(drop=True)
    Re = e[ASSETS].pct_change().values
    ice = e["date"].dt.isocalendar(); wke = ice.week.values + ice.year.values * 100
    checke = np.r_[True, wke[1:] != wke[:-1]]

    def build_recon(lbs):
        l1, l3, l6, l12 = lbs
        def mm(px):
            pp = px.values.astype(float); n = len(pp); o = np.full(n, np.nan)
            for t in range(l12, n):
                o[t] = (12*(pp[t]/pp[t-l1]-1) + 4*(pp[t]/pp[t-l3]-1) + 2*(pp[t]/pp[t-l6]-1) + 1*(pp[t]/pp[t-l12]-1))/4
            return o
        M = {a: mm(e[a]) for a in ["QQQ", "SHV", "TLT", "DBC", "GLD", "SPY", "TIP"]}
        n = len(e); tg = np.full((n, 6), np.nan)
        for t in range(n):
            if any(np.isnan(M[a][t]) for a in M):
                continue
            rO = (M["SPY"][t] > 0 and M["TIP"][t] > 0); can = (M["TIP"][t] > 0 and M["QQQ"][t] > 0)
            pos = {a: max(0, M[a][t]) for a in ["SHV", "TLT", "DBC", "GLD"]}; ds = sum(pos.values())
            dw = {a: (pos[a]/ds if ds > 0 else (1.0 if a == "SHV" else 0.0)) for a in pos}
            pq = max(0, M["QQQ"][t]); qsh = (pq)/(pq+ds) if (pq+ds) > 0 else 0
            qd = min(0.5, qsh) if can else 0.0; qb = ((1.0 if can else 0.0)+qd)/2
            w = {a: 0.0 for a in ASSETS}; w["SPY"] += 1.0 if rO else 0.0; w["SHV"] += 0.0 if rO else 1.0
            w["QQQ"] += qd+qb
            for a in ["SHV", "TLT", "DBC", "GLD"]:
                w[a] += (1-qd)*dw[a]+(1-qb)*dw[a]
            for a in ASSETS:
                tg[t, ASSETS.index(a)] = w[a]/3.0
        return tg

    print("lookbacks              CAGR  Sharpe  MaxDD")
    for nm, lbs in [("17/50/101/202 (-20%)", [17, 50, 101, 202]),
                    ("21/63/126/252 (base)", [21, 63, 126, 252]),
                    ("25/76/151/302 (+20%)", [25, 76, 151, 302])]:
        r = ratios(sim(build_recon(lbs), Re, checke, 8)[0])
        print("%-22s %5.1f  %.2f  %6.1f" % (nm, r["CAGR"], r["Sharpe"], r["MaxDD"]))


if __name__ == "__main__":
    main()
