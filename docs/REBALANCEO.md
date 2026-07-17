# Guía de rebalanceo de CENTINELA

La regla canónica es **chequeo semanal + banda de deriva del 8%**. Esta página
justifica cada pieza de esa regla con los números, y da la rutina paso a paso.

## 1. ¿Cada cuánto? — comparativa de frecuencias

Mismo combo, misma ventana (2015–2026), distintas cadencias de chequeo, con tres
niveles de coste por rotación:

| Frecuencia | Coste | CAGR | Sharpe | Sortino | MaxDD | Rotación/año |
|---|---|---:|---:|---:|---:|---:|
| Diaria | 5 pb | 13.3% | 1.44 | 1.77 | −9.3% | 17.5x |
| Diaria | 10 pb | 12.4% | 1.35 | 1.65 | −9.3% | 17.5x |
| Diaria | 20 pb | 10.4% | 1.15 | 1.42 | −9.9% | 17.5x |
| **Semanal** | 5 pb | 13.5% | 1.44 | 1.75 | −11.2% | 6.9x |
| **Semanal** | **10 pb** | **13.1%** | **1.40** | **1.70** | **−11.4%** | **6.9x** |
| **Semanal** | 20 pb | 12.3% | 1.33 | 1.61 | −11.7% | 6.9x |
| Mensual | 5 pb | 11.6% | 1.23 | 1.49 | −11.2% | 3.1x |
| Mensual | 10 pb | 11.4% | 1.21 | 1.47 | −11.3% | 3.1x |
| Mensual | 20 pb | 11.0% | 1.18 | 1.43 | −11.6% | 3.1x |

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

Barrido del umbral (chequeo semanal, neto 10 pb):

| Banda | Sharpe | Operaciones/año | Peor año |
|---:|---:|---:|---:|
| 0% (siempre) | 1.33 | 52 | positivo |
| 3% | 1.33 | 42 | positivo |
| 5% | 1.32 | 36 | positivo |
| **8%** | **1.35** | **28** | **positivo** |
| 10% | 1.33 | 24 | positivo |
| 12% | 1.34 | 22 | positivo |
| 15% | 1.34 | 19 | positivo |
| 20% | 1.33 | 16 | **−1.2%** |
| 30% | 1.20 | 13 | **−1.8%** |

**Lecturas:**
- Entre **5% y 15%** hay una meseta plana: el valor exacto da igual (señal de que
  no está sobreajustado). El 8% está en el centro.
- La banda **recorta las operaciones a la mitad** (52 → ~23-28/año) sin coste de
  rendimiento → menos comisiones, menos impuestos, menos trabajo.
- **No pasar del 15%**: a partir de ~20% dejas la cartera derivar demasiado, te
  pierdes cambios de régimen y el peor año se vuelve negativo.
- Verificado además por walk-forward: re-elegir la banda cada año con solo datos
  pasados da el mismo resultado que dejarla fija en 8% (ver ROBUSTEZ.md §3).

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
