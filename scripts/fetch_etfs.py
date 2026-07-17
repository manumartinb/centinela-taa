"""fetch_etfs.py - Descarga adjusted close (total-return) de los ETFs de las estrategias
TAA del CSV de TradingView. Ejecutar via PowerShell (Bash sin red). ASCII puro."""
import os
import yfinance as yf

TICKERS = ["QQQ", "SHV", "TLT", "DBC", "GLD", "SPY", "TIP"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ANALISIS", "OUTPUT", "data", "etf_adjclose.csv")

df = yf.download(TICKERS, start="2015-01-01", end="2026-07-31", auto_adjust=True, progress=False)
close = df["Close"] if "Close" in df.columns.get_level_values(0) else df
close = close[[t for t in TICKERS if t in close.columns]]
close.index.name = "date"
close.to_csv(OUT)
print("guardado:", OUT)
print("rango:", close.index.min().date(), "->", close.index.max().date(), "| filas", len(close))
print("cobertura por ticker (primer dato no-NaN):")
for t in close.columns:
    fv = close[t].first_valid_index()
    print("  %-4s desde %s  (%d validos)" % (t, fv.date() if fv is not None else "NA", close[t].notna().sum()))
