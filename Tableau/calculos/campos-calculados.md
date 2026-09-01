# Campos calculados del tablero

Definiciones exactas de los campos calculados del libro de Tableau, en el dialecto de
fórmulas de Tableau. Copiar y pegar tal cual en *Análisis → Crear campo calculado*.

---

## La regla que gobierna todas las fórmulas

**Ningún campo calculado usa `AVG()` sobre una columna del extracto. Todos son cocientes
de sumas.**

El motivo es el mismo por el que los extractos guardan sumas y conteos en lugar de
promedios: **el promedio de un conjunto de promedios no es el promedio del conjunto**,
salvo que todos los grupos tengan idéntico tamaño.

Un ejemplo concreto con datos reales del proyecto:

| Estado | Incendios | Acres | Acres por incendio |
|---|---:|---:|---:|
| Alaska | 12.843 | 32.233.094 | 2.509,78 |
| California | 189.550 | 12.745.859 | 67,24 |

- **Promedio de los promedios** (incorrecto): (2.509,78 + 67,24) / 2 = **1.288,51**
- **Cociente de sumas** (correcto): (32.233.094 + 12.745.859) / (12.843 + 189.550) = **222,28**

La diferencia es de casi seis veces. Como Alaska tiene quince veces menos incendios que
California, no puede pesar lo mismo en el promedio conjunto.

Por eso, el campo `[Acres promedio por incendio]` se define como
`SUM([Acres]) / SUM([N incendios])` y **nunca** como `AVG([Acres])`. Al estar definido
como cociente de sumas, Tableau lo recalcula correctamente en cualquier nivel de
agregación: por estado, por año, por origen o para el total general.

---

## Fuente `hechos_incendios`

### 1. Acres promedio por incendio

```
SUM([Acres]) / SUM([N incendios])
```

Severidad media del incendio en el nivel de agregación activo. **Medida central de la
comparación entre orígenes.** Formato sugerido: número con 2 decimales.

Valor esperado en el total general: **74,52 acres**.

### 2. Hectáreas promedio por incendio

```
SUM([Hectareas]) / SUM([N incendios])
```

La misma medida en unidades del sistema métrico, para contraste con literatura
internacional. Formato: número con 2 decimales.

### 3. % de grandes incendios

```
SUM([N grandes incendios]) / SUM([N incendios])
```

Proporción de incendios de clase F o G (1.000 acres o más). Formato: porcentaje con 2
decimales.

Valor esperado en el total general: **0,61 %** (11.559 de 1.880.465).

### 4. % de eventos sobre el total

```
SUM([N incendios]) / TOTAL(SUM([N incendios]))
```

Participación de cada categoría en el número total de incendios. Es un **cálculo de
tabla**: `TOTAL()` opera sobre el panel completo, de modo que el porcentaje siempre
suma 100 % dentro de la vista. Formato: porcentaje con 2 decimales.

### 5. % de acres sobre el total

```
SUM([Acres]) / TOTAL(SUM([Acres]))
```

Participación de cada categoría en la superficie total quemada. Junto con el campo
anterior, **construye el hallazgo central del estudio**: enfrentados en un mismo
gráfico, revelan que frecuencia y magnitud apuntan en direcciones opuestas.

Formato: porcentaje con 2 decimales.

### 6. Índice de severidad relativa

```
([Acres promedio por incendio]) / TOTAL(SUM([Acres]) / SUM([N incendios]))
```

Cuántas veces la severidad media de una categoría supera a la severidad media del
conjunto. Un valor de 4,19 en el origen natural significa que sus incendios queman, en
promedio, 4,19 veces más que el incendio medio del país. Formato: número con 2
decimales.

### 7. Etiqueta de origen abreviada

```
CASE [Origen del fuego]
  WHEN "Antropico"      THEN "Humano"
  WHEN "Natural"        THEN "Natural"
  WHEN "No determinado" THEN "Sin determinar"
END
```

Etiqueta corta para ejes estrechos y para las tarjetas de KPI, donde el texto completo
no cabe. Campo de dimensión.

### 8. Clase ordenada

```
STR([Orden de clase]) + ". " + [Clase de tamano]
```

Fuerza el orden correcto de las clases NWCG en los ejes (`1. A`, `2. B`, …, `7. G`).
Sin este campo, Tableau ordena las letras alfabéticamente, lo que coincide por
casualidad en este caso pero dejaría de hacerlo si se añadieran clases nuevas. Campo de
dimensión.

---

## Fuente `focos_muestra`

### 9. Tamaño visual del foco

```
LOG(SUM([Acres]) + 1)
```

Escala logarítmica para el tamaño de la marca en el mapa de puntos.

La superficie de los incendios abarca **ocho órdenes de magnitud**: desde 0,0001 hasta
606.945 acres. Con una codificación lineal, el incendio mediano (1 acre) sería 606.945
veces más pequeño que el mayor y resultaría literalmente invisible; el mapa mostraría
tres o cuatro círculos gigantes sobre un fondo vacío. El logaritmo comprime esa escala y
hace legible la distribución completa.

> El extracto ya trae precalculada la columna `Peso logaritmico`. Este campo calculado
> es una alternativa equivalente para quien prefiera controlar la transformación desde
> el propio libro.

### 10. Categoría de magnitud del foco

```
IF   [Acres] >= 5000 THEN "Muy grande (clase G)"
ELSEIF [Acres] >= 1000 THEN "Grande (clase F)"
ELSEIF [Acres] >= 100  THEN "Mediano (clases D-E)"
ELSEIF [Acres] >= 10   THEN "Pequeno (clase C)"
ELSE "Conato (clases A-B)"
END
```

Agrupación de la magnitud para filtrar el mapa sin arrastrar la dimensión completa de
clases. Campo de dimensión.

---

## Resumen de verificación

Tras crear los campos, comprobar que el libro reproduce estas cifras en el total
general. Si alguna discrepa, el error está casi siempre en haber usado `AVG()` en lugar
de un cociente de sumas.

| Medida | Valor esperado |
|---|---:|
| `SUM([N incendios])` | 1.880.465 |
| `SUM([Acres])` | 140.132.550 |
| `[Acres promedio por incendio]` | 74,52 |
| `[% de grandes incendios]` | 0,61 % |
| `[Acres promedio por incendio]` filtrado a *Antrópico* | 26,95 |
| `[Acres promedio por incendio]` filtrado a *Natural* | 312,54 |
