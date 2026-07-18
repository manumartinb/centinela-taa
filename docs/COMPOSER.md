# Llevar CENTINELA a Composer Trade

**¿Se puede?** Sí — Composer es un encaje natural para una rotación tipo HAA. Pero
hay que ser honesto: **NO es un port bit-exacto**, es una adaptación fiel-en-espíritu.
La symphony lista para importar está en [`../composer/CENTINELA_symphony.json`](../composer/CENTINELA_symphony.json).

## Cómo funciona Composer (en 30 segundos)

Una *symphony* es un **árbol** que se evalúa cada día de rebalanceo:
- **Nodos de peso**: `wt-cash-equal` (equipondera sus hijos), `wt-cash-specified`
  (pesos fijos), `wt-inverse-volatility`, `wt-market-cap`. *(Solo estos cuatro.)*
- **Condiciones**: `if` → dos `if-child` (rama "then" con la condición, rama "else").
  La condición es una comparación binaria `lhs (fn, ventana) [gt/lt] rhs`.
- **Funciones (indicadores)**: `cumulative-return`, `moving-average-price`,
  `exponential-moving-average-price`, `current-price`, `relative-strength-index`,
  `standard-deviation-return`, `max-drawdown`… todas de **una sola ventana**.
- **Activos**: nodo hoja con `ticker`.
- **Rebalanceo**: calendario (`daily`/`weekly`/`monthly`/…) **o** *threshold*
  (rebalancea cuando la deriva supera un % — el equivalente a nuestra banda).

## Lo que SÍ se traslada fiel

- **Universo**: QQQ, SPY, SHV, TLT, DBC, GLD + **TIP como canario**.
- **Estructura ⅓ + ⅓ + ⅓**: `wt-cash-equal` de las tres sub-estrategias.
- **Régimen SPY-or-Cash**: `if mom(TIP)>0 y mom(SPY)>0 → SPY, si no → SHV`
  (el "y" se hace con `if` anidados).
- **Rebalanceo semanal** (`"rebalance": "weekly"`) o **threshold ≈ 8%** (nuestra banda).

## Lo que NO se puede reproducir (los 3 muros)

1. **Momentum 13612W**. Es una media ponderada de 4 ventanas (1/3/6/12 meses, pesos
   12/4/2/1). Composer solo compara **una ventana** por condición; no se puede sumar
   ni promediar cuatro. → Se aproxima con `cumulative-return` de **una sola ventana**
   (aquí 21 días = 1 mes, que es el 63% del peso del 13612W, y lo que usa la mayoría
   de ports de HAA en Composer).
2. **Reparto proporcional al momentum**. CENTINELA reparte la defensa proporcional a
   `max(0, mom)` y sizing fraccional de QQQ. Composer solo tiene equal/fijo/inv-vol/
   market-cap. → Se aproxima con **equal-weight de sleeves condicionales** (cada
   activo entra si su momentum >0, si no a cash).
3. **Por tanto es un PRIMO, no un clon**. La lógica y el universo son los mismos,
   pero la matemática difiere. **Los números de TradingView (Sharpe 1.41, MaxDD −9%)
   NO transfieren 1:1** — hay que **backtestear la symphony DENTRO de Composer** y
   juzgarla con sus propios resultados.

## Estructura de la symphony (mapa)

```
root  (rebalanceo semanal)
└── wt-cash-equal            ← ⅓ / ⅓ / ⅓
    ├── SPY-or-Cash          if TIP>0 y SPY>0 → SPY ; si no → SHV
    ├── Defense First        wt-cash-equal de 4 sleeves:
    │     ├── QQQ  (canario TIP>0 y QQQ>0 → QQQ ; si no SHV)
    │     ├── TLT  (mom>0 → TLT ; si no SHV)
    │     ├── DBC  (mom>0 → DBC ; si no SHV)
    │     └── GLD  (mom>0 → GLD ; si no SHV)
    └── Blend 50/50          wt-cash-equal de:
          ├── QQQ agresivo   (canario TIP>0 y QQQ>0 → QQQ ; si no SHV)
          └── Defense First  (mismo bucket de arriba)
```

Momentum: `cumulative-return`, ventana **21 días**, comparado con **0** (momentum
absoluto). Es el parámetro a ajustar (ver abajo).

## Cómo importar y qué hacer después

1. En Composer: **Create → Import symphony** (o pega el JSON en el editor).
2. **Backtestea DENTRO de Composer** (su motor, sus datos). No asumas los números de
   aquí.
3. **Barre la ventana de momentum** (21 / 63 / 126 días) y quédate con la que mejor
   se comporte *en el backtest de Composer* — la de 21d es whippy (más señal de
   1 mes); una más larga da menos rotación pero menos reactividad.
4. **Rebalanceo**: prueba `weekly` (calendario) frente a `threshold` con deriva ~8%
   (Trading Settings → Threshold). El threshold es lo más parecido a nuestra banda
   y suele reducir operaciones y coste.
5. Compara el resultado de Composer con el dossier de TradingView; espera diferencias
   por las aproximaciones de los 3 muros.

## Ejemplo de referencia del usuario (comparación)

La symphony "V2 GPT 5.2 Max HAA 60/40 + Defense First" que ya tenías es un primo
válido, pero: usa QQQ como equity (sin la pata SPY), añade filtros extra (UUP, y una
puerta HYG vs su EMA-100) que CENTINELA no tiene, y rebalancea a diario. La versión
de aquí es más fiel a CENTINELA (pata SPY incluida, canario TIP limpio, ⅓/⅓/⅓,
semanal), sin los filtros de más.

---

*Fuentes Composer:* [Cómo funcionan las symphonies](https://www.composer.trade/learn/how-composer-symphonies-work) ·
[Threshold trading](https://help.composer.trade/article/76-threshold-trading) ·
[Asignar pesos](https://help.composer.trade/article/18-symphony-editor-assign-weights)
