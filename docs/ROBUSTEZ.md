# Batería de robustez de CENTINELA — detalle completo

> **Actualización 2026-07:** CENTINELA fue además sometida a la prueba máxima — dos
> campañas pre-registradas de búsqueda masiva (685 configuraciones retadoras, 25 ETFs,
> 19 años con la GFC incluida, con Deflated Sharpe Ratio y ledger anti data-mining) —
> y **ninguna retadora la batió**. Ver [CICLO_COMPLETO.md](CICLO_COMPLETO.md).

Todo lo que se hizo para intentar **tumbar** la estrategia antes de darla por buena.
Configuración evaluada: pesos exactos, chequeo semanal (primer día ISO) + banda 8%,
neto 10 pb por rotación, ventana 2015-03 → 2026-07 (N=2.843 días).

## 1. Métricas base (recomputadas y auditadas al decimal)

```
CAGR 13.03% · Sharpe 1.409 · Sortino 1.717 · Calmar 1.439 · MaxDD −9.05% · Vol 8.98%
Turnover 6.36x/año · ~23 rebalanceos/año
IS (≤2024): CAGR 11.7%, Sharpe 1.31  |  OOS (2025+): CAGR 22.0%, Sharpe 1.94
```

Un peritaje externo independiente (otra IA, con acceso a datos y scripts) recomputó
el pipeline completo y reprodujo cada ratio con diferencias < 0.01 (redondeo).

## 2. Significancia estadística

### 2.1 Bootstrap del Sharpe (2.000 iteraciones)
- iid por día: CI95 **[0.82, 2.01]**
- Por bloques mensuales (respeta autocorrelación): CI95 **[0.87, 1.95]**
- Cota inferior ≫ 0 en ambos → el Sharpe positivo no es artefacto muestral.

### 2.2 Diferencia de Sharpe vs SPY (bootstrap pareado por bloques mensuales)
- Diferencia: **+0.59**
- CI95: **[+0.09, +1.07]**
- **p(diferencia ≤ 0) = 0.009** → la superioridad riesgo-ajustada sobre el S&P 500
  es estadísticamente significativa al 1%.

### 2.3 Regresión diaria vs SPY
- **Beta 0.28** (expuesta a bolsa solo un cuarto)
- **Alpha anualizado +8.5%/año**
- Information Ratio −0.13 (recordatorio honesto: en retorno bruto no gana a SPY;
  su valor es el perfil de riesgo, no el exceso bruto).

### 2.4 Null de timing (permutación, leakage-free, 2.000 iteraciones)
¿La secuencia temporal de decisiones aporta, o daría igual asignar esos mismos
pesos en fechas aleatorias?
- Sharpe real (pesos rezagados 1 día): **1.48**
- Distribución nula (semanas permutadas): 0.90 ± 0.15
- **p = 0.0000** (0 de 2.000 permutaciones lo alcanzan) → el timing añade valor real.
- Nota de integridad: una primera versión de este test tenía un look-ahead de 1 día
  (detectado por el peritaje externo). El resultado de arriba es la versión
  corregida, estrictamente leakage-free.

## 3. Anti-overfitting (walk-forward con re-selección)

¿Están los parámetros ajustados al pasado? Test: cada año, re-elegir la banda de
deriva usando **solo datos anteriores** a ese año, y evaluar en el año (OOS puro):

| Año test | Banda elegida (train) | OOS re-selec. | OOS banda fija 8% |
|---|---|---:|---:|
| 2018 | 15% | +5.2% | +5.8% |
| 2019 | 15% | +18.0% | +17.5% |
| 2020 | 15% | +29.0% | +29.4% |
| 2021 | 15% | +15.2% | +16.2% |
| 2022 | 10% | −2.3% | −1.8% |
| 2023 | 10% | +23.4% | +22.8% |
| 2024 | 10% | +12.9% | +12.1% |
| 2025 | 15% | +23.0% | +20.7% |
| 2026 | 15% | +10.4% | +11.7% |
| **Agregado (9 años)** | — | **Sharpe 1.52 / CAGR 15.5%** | **Sharpe 1.52 / CAGR 15.5%** |

**Idénticos.** La elección de la banda no aporta información del futuro: no hay
sobreajuste en ese parámetro.

### Perturbación de parámetros
- **Pesos del combo** (⅓/⅓/⅓ → mezclas 0.2–0.5): Sharpe 1.38–1.43, MaxDD −8.9/−9.5.
  Meseta plana: el reparto equitativo no está "fitteado".
- **Banda de deriva** 0/3/5/8/10/12/15%: Sharpe 1.32–1.44 (meseta). Techo real en
  ~20% (a partir de ahí el peor año se vuelve negativo).
- **Lookbacks del momentum ±20%** (17/50/101/202 y 25/76/151/302): Sharpe 1.11–1.21
  vs 1.35 base. Único parámetro sensible — pero (a) son el estándar publicado de
  Keller (1/3/6/12 meses), no una elección nuestra, y (b) incluso perturbados la
  estrategia sigue funcionando (sin colapso).

## 4. Estrés de ejecución

| Estrés | Resultado |
|---|---|
| Ejecutar con +1 día de retraso | Sharpe 1.41 → 1.33; MaxDD −9.1 → −11.6 (degrada con gracia) |
| Coste 5 pb | Sharpe 1.44 |
| Coste 10 pb (base) | Sharpe 1.41 |
| Coste 20 pb | Sharpe 1.34 |
| Coste 30 pb | Sharpe 1.27 |
| Día de rebalanceo (L/M/X/J/V) | Sharpe 1.36 / 1.39 / 1.43 / 1.43 / 1.40 |

## 5. Sub-períodos y regímenes

| Período | CENTINELA (CAGR / Sharpe / MaxDD) | SPY |
|---|---|---|
| 2015–2019 (alcista tranquilo) | 8.1% / 1.31 / −4.9% | 11.6% / 0.88 / −19.3% |
| 2020–2022 (COVID + inflación) | **13.9% / 1.21 / −9.1%** | 7.6% / 0.42 / −33.7% |
| 2023–2026 (alcista fuerte) | 19.4% / 1.82 / −9.0% | 22.8% / 1.43 / −18.8% |

Patrón claro y coherente con el diseño: pierde algo en los alcistas, gana mucho
en los turbulentos, y su Sharpe es superior en **todos** los sub-períodos.

## 6. El combo vs sus componentes

| Estrategia | CAGR | Sharpe | MaxDD | Calmar |
|---|---:|---:|---:|---:|
| S1 SPY-or-Cash | 12.4% | 1.23 | −12.4% | 0.99 |
| S2 Defense First | 11.9% | 1.24 | −10.3% | 1.15 |
| S3 Blend 50/50 | 14.1% | 1.27 | −14.2% | 0.99 |
| HAA pura | 15.6% | 1.09 | −23.7% | 0.66 |
| **CENTINELA** | 13.0% | **1.41** | **−9.1%** | **1.44** |

Mejor Sharpe, MaxDD y Calmar que cualquier componente: la mezcla aporta de verdad.

## 7. Limitaciones reconocidas

1. **Ventana 2015–2026 mayormente alcista**: contiene UNA crisis inflacionaria
   (2021-22) y UN crash deflacionario (2020). La cobertura de regímenes extremos
   es fina; por eso se mantienen TLT y DBC aunque en muestra aporten poco.
2. **Survivorship suave**: el universo (6 ETFs grandes) se eligió sabiendo que
   existieron y funcionaron. Mitigado por ser índices mayores, no descartado.
3. **Lag del momentum**: tras un rebote en V la estrategia reentra tarde. En
   subidas verticales irá por detrás — coste estructural del seguro.
4. **Sensibilidad de fuente de datos en el filo**: cuando `mom(TIP) ≈ 0`, dos
   proveedores de precios pueden dar señales opuestas (los ajustes de dividendos
   difieren). Caso real 2026-07: una fuente decía RISK-OFF y la exacta RISK-ON.
   Regla operativa: decidir con el cálculo exacto; el indicador avisa (`!FILO`).
5. **OOS corto**: 2025–2026 (~1.5 años). El Sharpe OOS 1.94 es pequeño-N.
6. Costes modelados planos (10 pb/rotación); sin fiscalidad ni slippage extremo.
7. **Reconstrucción residual dentro del "exacto"**: la fuente da los pesos exactos
   de Defense First completos y el peso QQQ exacto de las tres estrategias, pero
   NO el desglose defensivo de la sub-estrategia Blend — ese se reconstruye
   proporcional al reparto de Defense First (supuesto razonable y documentado en
   `scripts/backtest_taa.py`). Afecta solo a cómo se reparte la fracción defensiva
   de ⅓ de la cartera; el nivel de riesgo (QQQ/SPY vs defensa) es exacto.
