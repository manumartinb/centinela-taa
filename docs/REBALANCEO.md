# Guía de rebalanceo de CENTINELA

La regla canónica es **chequeo semanal + banda de deriva del 8%**. Esta página
justifica cada pieza de esa regla con los números, y da la rutina paso a paso.

## 1. ¿Cada cuánto? — comparativa de frecuencias

Mismo combo, misma ventana (2015–2026), distintas cadencias de chequeo, con tres
niveles de coste por rotación:

*(Pesos EXACTOS; chequeo = primer día de cada periodo; diaria sin banda, semanal y
mensual con banda 8% — la convención canónica. Recalculado en auditoría 2026-07-18.)*

| Frecuencia | Coste | CAGR | Sharpe | MaxDD | Operaciones/año |
|---|---|---:|---:|---:|---:|
| Diaria | 5 pb | 13.3% | 1.44 | −9.3% | ~252 |
| Diaria | 10 pb | 12.4% | 1.35 | −9.3% | ~252 |
| Diaria | 20 pb | 10.4% | 1.15 | −9.9% | ~252 |
| **Semanal + banda 8%** | 5 pb | 13.4% | 1.44 | −9.1% | ~23 |
| **Semanal + banda 8%** | **10 pb** | **13.0%** | **1.41** | **−9.1%** | **~23** |
| **Semanal + banda 8%** | 20 pb | 12.3% | 1.34 | −9.1% | ~23 |
| Mensual + banda 8% | 5 pb | 11.6% | 1.23 | −14.2% | ~9 |
| Mensual + banda 8% | 10 pb | 11.5% | 1.21 | −14.2% | ~9 |
| Mensual + banda 8% | 20 pb | 11.2% | 1.18 | −14.2% | ~9 |

**Lecturas:**
- **Diaria**: solo gana con costes irreales (5 pb). A costes normales, las
  comisiones se comen la ventaja; a 20 pb es la PEOR opción.
- **Mensual**: pierde ~2 puntos de CAGR y ~0.2 de Sharpe — la señal de momentum
  envejece demasiado entre chequeos. Su única virtud es la comodidad.
- **Semanal**: retiene el rendimiento del diario con un tercio de la rotación, y
  es **la más robusta al coste real**. → **Elegida.**

## 2. ¿Qué día de la semana? — barrido completo

Sharpe del combo según el día fijo de rebalanceo (neto 10 pb):

| Lunes | Martes | Miércoles | Jueves | Viernes |
|---:|---:|---:|---:|---:|
| 1.36 | 1.39 | **1.43** | **1.43** | 1.40 |

Y en un barrido anterior con otra métrica de detalle, el viernes mostró el peor
MaxDD (−11.4% vs −9/−10% del resto): rebalancear justo antes del fin de semana te
deja la cartera recién tocada expuesta al gap del lunes.

**Conclusión:** la estrategia NO depende del día (todas ~1.4 — buena señal de
robustez), pero si hay que elegir: **miércoles o jueves**, y evitar viernes.
Lo importante es que sea **siempre el mismo día**.

## 3. La banda de deriva — rebalanceo "por hito"

En vez de rebalancear cada chequeo sí o sí, solo se actúa si la cartera se ha
desviado del objetivo más que un umbral:

```
desviación = ½ · Σ_activos | peso_actual − peso_objetivo |
actuar solo si desviación > banda
```

Barrido del umbral sobre los pesos EXACTOS (chequeo semanal, neto 10 pb;
recalculado en auditoría 2026-07-18):

| Banda | Sharpe | CAGR | MaxDD | Operaciones/año | Peor año |
|---:|---:|---:|---:|---:|---:|
| 0% (siempre) | 1.40 | 12.9% | −9.2% | 52 | −2.3% |
| 3% | 1.40 | 12.9% | −9.2% | 45 | −2.3% |
| 5% | 1.40 | 12.9% | −9.1% | 32 | −2.5% |
| **8%** | **1.41** | **13.0%** | **−9.1%** | **23** | **−2.1%** |
| 10% | 1.44 | 13.3% | −9.1% | 18 | −2.3% |
| 12% | 1.44 | 13.3% | −9.3% | 16 | −2.2% |
| 15% | 1.45 | 13.5% | −9.4% | 14 | −2.4% |
| 20% | 1.42 | 13.1% | −9.3% | 12 | **−3.6%** |
| 30% | 1.41 | 13.4% | −10.2% | 10 | **−3.5%** |

**Lecturas:**
- Entre **0% y 15%** hay una meseta (Sharpe 1.40–1.45): el valor exacto da igual —
  señal de que la banda no está sobreajustada. Las diferencias dentro de la meseta
  (8 vs 10 vs 15) son ruido muestral; el walk-forward lo confirma (re-elegir la
  banda cada año con solo datos pasados da lo mismo que fijarla — ROBUSTEZ.md §3).
- La banda **recorta las operaciones a la mitad o más** (52 → 23 con el 8%; → 14
  con el 15%) sin coste de rendimiento → menos comisiones, impuestos y trabajo.
- **A partir de ~20% el peor año se degrada** (−2.1% → −3.6%): dejas la cartera
  derivar demasiado y te pierdes cambios de régimen. No pasar del 15%.
- El **8% es el default canónico** (validado también en el barrido de la
  reconstrucción, donde la meseta 5–15% se repite con niveles de Sharpe menores).

## 4. La rutina operativa completa

**Cada miércoles (o jueves), tras el cierre — 2 minutos:**

1. Abre el gráfico **diario** con el indicador (o tu cálculo exacto).
2. Lee los **pesos objetivo** de la tabla (QQQ / SPY / SHV / TLT / DBC / GLD).
3. El indicador ya calcula la **Desviación** y te dice la **ACCIÓN**:
   - `mantener` → cierra y hasta la semana que viene (la mayoría de las semanas).
   - `REBALANCEAR` → compra/vende hasta clavar los pesos objetivo.
4. Si aparece **`!FILO`** (canario TIP pegado a cero): el régimen es frágil y el
   indicador puede discrepar del cálculo exacto → confirma con el exacto antes
   de mover dinero.
5. Ejecuta a mercado cerca del cierre (o al día siguiente a la apertura: el
   backtest con +1 día de retraso apenas degrada — Sharpe 1.41 → 1.33).

**Notas prácticas:**
- Usa órdenes de mercado en ETFs líquidos; el coste real esperado (spread+comisión)
  en estos 6 ETFs está más cerca de 5 pb que de 20 pb.
- Fracciones: si tu broker no permite fracciones, redondea al entero de acciones
  más cercano; con la banda del 8% el error de redondeo es irrelevante.
- Aportaciones nuevas: aprovéchalas para rebalancear "gratis" (comprar lo que
  esté por debajo del objetivo).
- Fiscalidad: la banda + semanal minimiza ventas; aun así, en cuentas sujetas a
  plusvalías considera priorizar los ajustes vía aportaciones.

## 5. Resumen de la regla canónica

> **Chequeo semanal (miércoles o jueves, al cierre) + banda de deriva 8%.**
> Resultado esperado: ~23 operaciones/año, Sharpe ~1.4, y la mayoría de semanas
> sin tocar nada.
