# ¿Por qué estos 6 activos? — el caso de DBC (materias primas)

Una pregunta razonable y frecuente: **"DBC ha rendido regular toda su vida. ¿Por
qué lo tenemos en el combo si no gana?"** La respuesta es un buen ejemplo de la
filosofía de toda la estrategia, así que merece su propia página.

## 1. Es verdad: DBC solo es mediocre

Comprar y mantener DBC (índice diversificado de materias primas) 2015–2026:

| Métrica | DBC buy & hold |
|---|---|
| Multiplicador | x1.89 |
| CAGR | **5.8%** |
| Sharpe | **0.41** |
| Peor caída (MaxDD) | **−41.7%** |

Como inversión pasiva, es floja: gana poco y cae mucho. La intuición de "esto no
aporta" es correcta… **para comprar-y-mantener**.

## 2. Pero el combo no lo compra-y-mantiene: lo *cronometra*

CENTINELA solo carga DBC cuando su momentum es positivo. Y ese filtro funciona:

> **DBC durante los periodos en que el combo lo tiene: +7.9%/año**
> DBC en general (siempre): +5.8%/año

El momentum le pilla las buenas rachas (inflación, tensión de oferta) y esquiva
los tramos muertos. Convierte un activo del montón en uno que suma.

Cuánto pesa en la práctica: peso medio **7.8%**, mediana 6.2%, máximo 25.8%. No es
una posición grande — es un seguro modesto que se agranda cuando toca.

## 3. Efecto neto en el combo: POSITIVO

Combo con DBC vs combo sin DBC (su peso reasignado a liquidez), regla semanal +
banda 8%, neto 10 pb:

| | CON DBC | SIN DBC |
|---|---:|---:|
| CAGR | **13.0%** | 12.2% |
| Sharpe | **1.41** | 1.39 |
| MaxDD | −9.1% | −8.9% |
| **Peor año** | **−2.1%** | **−5.0%** |

Quitarlo cuesta **−0.8 pp de CAGR** y, sobre todo, **empeora el peor año en 2.9 pp**.

## 4. El desglose que lo explica todo

![Aporte de DBC por año](../charts/dbc_contribution.png)

| Año | Aporte de DBC al combo |
|---|---:|
| 2015 | −0.3 |
| 2016 | −0.2 |
| 2017 | −0.2 |
| 2018 | −0.2 |
| 2019 | +0.4 |
| 2020 | +0.8 |
| **2021** | **+4.9** ← inflación |
| **2022** | **+3.3** ← el año que el S&P hizo −18% |
| 2023 | −1.6 |
| 2024 | −0.7 |
| 2025 | −0.4 |
| **2026** | **+3.3** ← inflación |

En los años tranquilos DBC es un **lastre pequeño** (−0.2 a −1.6 pp): eso es lo que
se ve a simple vista. Pero en **2021, 2022 y 2026** aportó +4.9, +3.3 y +3.3. La
suma de sus tres rescates (~+11.5 pp) **triplica** la suma de todos sus lastres.

## 5. Su verdadero trabajo: estar en verde cuando todo cae

DBC no está para ganar la carrera larga. Está para ser lo que sube **cuando la
bolsa y los bonos caen a la vez**. En 2022 las acciones se hundieron (−18%), los
bonos largos (TLT) se hundieron *con* ellas (rompiendo su papel habitual de
refugio)… y las materias primas volaron. DBC fue, ese año, prácticamente **la
única pata en verde**. Convirtió lo que habría sido un −5.0% en un −1.8%.

Esa es la **diversificación de régimen**: metes un activo mediocre-de-media pero
**descorrelacionado en las crisis**, y dejas que el momentum lo cargue solo cuando
hace falta. El precio de ese seguro es un puntito en los años buenos. Barato.

## 6. Contraste honesto: ¿cuál SÍ es prescindible? — TLT

Para que no parezca que defendemos todos los activos por igual: el análogo de este
estudio para **TLT (bonos largos)** da el resultado opuesto. Quitar TLT **mejora**
ligeramente el Sharpe (1.42 vs 1.41) sin apenas tocar el CAGR, porque en 2022 falló
como refugio (cayó con la bolsa). TLT es el **verdadero candidato marginal**; DBC
se paga su sitio.

| Activo | ¿Aporta al combo? | Papel |
|---|---|---|
| QQQ, SPY | Sí (motor) | Retorno en régimen alcista |
| SHV | Sí (ancla) | Refugio universal / liquidez |
| **DBC** | **Sí (seguro inflación)** | El único verde en 2022 |
| GLD | Sí (diversificador clave) | Descorrelación consistente |
| TLT | Marginal | Seguro de crash deflacionario (2020), falló en 2022 |

**Conclusión:** se mantienen los 6. Si algún día se recorta por simplicidad, el
candidato es TLT — nunca DBC.

---

*Reproducible con `scripts/backtest_taa.py` + `scripts/apr_combo.py` sobre
`data/etf_adjclose.csv`. Ver también [ROBUSTEZ.md](ROBUSTEZ.md) §6.*
