# Fórmula completa de CENTINELA

Todo lo que hace la estrategia, paso a paso, sin cajas negras.

## Universo

| Ticker | Rol | ¿Se compra? |
|---|---|---|
| QQQ | Ofensivo (Nasdaq-100) | Sí |
| SPY | Equity de la pata SPY-or-Cash | Sí |
| SHV | Liquidez (letras del Tesoro 0-1 año) | Sí |
| TLT | Bonos largos del Tesoro (seguro deflación/crash) | Sí |
| DBC | Materias primas (seguro inflación) | Sí |
| GLD | Oro (diversificador clave) | Sí |
| **TIP** | **Canario de régimen — solo se LEE su momentum** | **No** |

## Paso 0 — Momentum "13612W/4" (Keller), para cada activo

Media ponderada de los retornos a 1, 3, 6 y 12 meses, con más peso a lo reciente:

```
mom(P) = ( 12·(P/P₍₂₁₎ − 1) + 4·(P/P₍₆₃₎ − 1) + 2·(P/P₍₁₂₆₎ − 1) + 1·(P/P₍₂₅₂₎ − 1) ) / 4
```

Lookbacks en días de trading: 21 (1m), 63 (3m), 126 (6m), 252 (12m). Se calcula
sobre **precios ajustados (total-return)** al cierre diario.

> Interpretación: `mom > 0` = tendencia alcista compuesta; `mom < 0` = bajista.

## Paso 1 — Régimen (sub-estrategia S1: SPY-or-Cash)

```
RISK-ON  ⇔  mom(SPY) > 0  Y  mom(TIP) > 0

S1 = 100% SPY   si RISK-ON
S1 = 100% SHV   si RISK-OFF
```

El canario TIP captura el régimen de tipos reales: cuando cae con tendencia,
históricamente vienen curvas — la estrategia se protege aunque la bolsa aún suba.

## Paso 2 — Reparto defensivo (común a S2 y S3)

Entre los 4 defensivos {SHV, TLT, DBC, GLD}, peso proporcional al momentum
positivo; si ninguno lo tiene, todo a liquidez:

```
pos_i = max(0, mom_i)
dsum  = Σ pos_i
dw_i  = pos_i / dsum        (si dsum > 0)
dw_SHV = 1, resto 0          (si dsum = 0)
```

## Paso 3 — Sizing de la pata ofensiva (QQQ)

```
canary = mom(TIP) > 0  Y  mom(QQQ) > 0      ← puerta de entrada al riesgo

# S-HAA (binaria):
qHAA = 1 si canary, 0 si no

# S2 Defense First (fraccional):
qShare = max(0,mom_QQQ) / ( max(0,mom_QQQ) + dsum )
qDEF   = min(0.5, qShare)   si canary;  0 si no

# S3 Blend 50/50 (media exacta de ambas):
qBLEND = (qHAA + qDEF) / 2
```

> Nota de fidelidad: en la implementación original de TradingView el sizing
> fraccional de Defense First se cuantiza a dieciseisavos (0, 1/16, 2/16, …).
> La forma `qShare` de arriba es la reconstrucción validada (correlación diaria
> 0.85 con la original; mismo CAGR). El régimen, el momentum y el Blend son
> **exactos** (verificados al 100% contra la fuente).

## Paso 4 — Las tres carteras

```
S1 = { SPY: 1 } o { SHV: 1 }                              (paso 1)
S2 = { QQQ: qDEF,   defensivos: (1−qDEF)·dw_i }
S3 = { QQQ: qBLEND, defensivos: (1−qBLEND)·dw_i }
```

## Paso 5 — CENTINELA = media de las tres

```
peso_activo = ( S1_activo + S2_activo + S3_activo ) / 3
```

Los pesos quedan en [0,1] y suman 1. La cartera está siempre 100% invertida
(la liquidez SHV cuenta como posición).

## Paso 6 — Regla de rebalanceo (canónica)

```
1. CHEQUEO semanal: un día fijo por semana, al cierre.
2. Entre chequeos los pesos DERIVAN con el mercado (no se toca la cuenta).
3. En el chequeo se calcula la desviación frente al objetivo del día:
      desviación = ½ · Σ |peso_actual − peso_objetivo|
4. REBALANCEAR solo si desviación > 8% (banda de deriva).
```

Ver [REBALANCEO.md](REBALANCEO.md) para la justificación empírica de cada elección.

## Por qué funciona (intuición)

1. **Momentum + canario**: el trend-following captura tendencias sostenidas; el
   canario corta la exposición ante estrés de tipos reales. El grueso del edge
   está en **evitar los grandes drawdowns**, no en acertar el timing fino.
2. **Diversificación de estilos de decisión**: tres reglas distintas (binaria,
   defensiva-fraccional, intermedia) promediadas — los errores de cada una se
   compensan (el combo supera en Sharpe/MaxDD a cualquiera por separado).
3. **Diversificación de regímenes**: oro, materias primas, bonos y liquidez
   cubren escenarios donde la bolsa sufre (inflación 2022 → DBC; crash
   deflacionario 2020 → TLT; siempre → GLD/SHV).
