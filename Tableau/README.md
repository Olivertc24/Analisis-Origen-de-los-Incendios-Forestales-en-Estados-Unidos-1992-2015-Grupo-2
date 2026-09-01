# Tablero de Tableau — Origen del fuego en Estados Unidos (1992–2015)

Tablero ejecutivo que acompaña al aplicativo de Streamlit. Mientras el aplicativo
presenta la investigación estadística en detalle, el tablero ofrece la **lectura visual
de las métricas macro** sobre los 1.880.465 incendios del período.

---

## Estado del entregable

| Componente | Estado |
|---|---|
| Extractos de datos (`extractos/*.csv`) | ✅ Generados y validados contra el Data Lake |
| Script generador de extractos | ✅ `generar_extractos.py`, reproducible |
| Documentación del modelo en Tableau | ✅ Este archivo |
| Campos calculados con su fórmula exacta | ✅ [`calculos/campos-calculados.md`](calculos/campos-calculados.md) |
| Registro de transformaciones | ✅ [`preparacion/transformacion-datos.md`](preparacion/transformacion-datos.md) |
| Libro `.twb` armado | ✅ `Origen_del_Fuego_EEUU_1992_2015.twb`, generado por código y verificado abriéndolo en Tableau Desktop |

**El libro está construido y verificado.** Se genera por código con
[`construir_libro.py`](construir_libro.py) y se comprobó abriéndolo en Tableau Desktop:
las tres páginas cargan y renderizan sin errores. La especificación de abajo documenta
lo que el libro contiene, y sirve además para reconstruirlo a mano si hiciera falta.

```bash
cd Tableau
python generar_extractos.py    # extractos desde el Data Lake, con control de consistencia
python construir_libro.py      # genera Origen_del_Fuego_EEUU_1992_2015.twb
```

---

## 1. Fuentes de datos del tablero

Los tres archivos de `extractos/` se generan con `generar_extractos.py`, que consulta el
Data Lake Parquet del proyecto y **verifica que los totales coincidan exactamente** con
los del aplicativo. Si el control de consistencia fallara, el script lo reporta.

| Archivo | Filas | Tamaño | Función en el tablero |
|---|---:|---:|---|
| `hechos_incendios.csv` | 245.653 | 23,6 MB | Fuente principal. Tabla de hechos agregada. |
| `focos_muestra.csv` | 40.000 | 3,0 MB | Muestra de incendios individuales para el mapa de puntos. |
| `resumen_origen.csv` | 3 | < 1 KB | Cuadro comparativo por origen, para las tarjetas de KPI. |

### 1.1. Estructura de `hechos_incendios.csv`

**Grano:** una fila por combinación de año, mes, estado, origen, causa, clase de tamaño
y sector de propiedad.

| Campo | Tipo | Rol en Tableau | Descripción |
|---|---|---|---|
| `Anio` | Entero | **Dimensión** | Año de detección (1992–2015) |
| `Mes` | Entero | **Dimensión** | Número de mes (1–12) |
| `Mes abrev` | Texto | Dimensión | Abreviatura de tres letras, para ejes |
| `Estacion` | Texto | Dimensión | Invierno / Primavera / Verano / Otoño |
| `Temporada de fuego` | Texto | Dimensión | Baja / Media / Alta |
| `Codigo estado` | Texto | Dimensión geográfica | Código de dos letras |
| `Estado` | Texto | Dimensión geográfica | Nombre completo |
| `Region censal` | Texto | Dimensión | Noreste / Medio Oeste / Sur / Oeste |
| `Origen del fuego` | Texto | Dimensión | **Variable segmentadora del estudio** |
| `Causa` | Texto | Dimensión | Una de las 13 causas NWCG |
| `Clase de tamano` | Texto | Dimensión | Letra A–G |
| `Orden de clase` | Entero | **Dimensión** | 1–7, para ordenar la clase correctamente |
| `Sector de propiedad` | Texto | Dimensión | Federal / Estatal / Privado / Tribal / Local / … |
| `N incendios` | Entero | Medida | Conteo de incendios |
| `Acres` | Real | Medida | Superficie quemada en acres |
| `Hectareas` | Real | Medida | Superficie quemada en hectáreas |
| `N grandes incendios` | Entero | Medida | Incendios de clase F o G |

> **Importante al conectar.** Tableau clasifica automáticamente `Anio`, `Mes` y
> `Orden de clase` como **medidas** por ser numéricos. Hay que **convertirlos a
> dimensión** manualmente (clic derecho → Convertir en dimensión). Si no se hace, los
> gráficos sumarán años en lugar de agruparlos.

### 1.2. Estructura de `focos_muestra.csv`

**Grano:** un incendio individual. Muestra aleatoria de 40.000 registros.

| Campo | Tipo | Rol | Notas |
|---|---|---|---|
| `Latitud` | Real | Medida → rol geográfico **Latitud** | Asignar el rol manualmente |
| `Longitud` | Real | Medida → rol geográfico **Longitud** | Asignar el rol manualmente |
| `Anio`, `Mes abrev`, `Origen del fuego`, `Causa`, `Estado`, `Clase de tamano` | — | Dimensiones | Contexto del punto |
| `Acres` | Real | Medida | Superficie real |
| `Peso logaritmico` | Real | Medida | `LOG10(acres + 1) + 0,15`. **Se usa para el tamaño de la marca** |

> **Por qué existe `Peso logaritmico`.** La superficie abarca ocho órdenes de magnitud
> (de 0,0001 a 606.945 acres). Codificarla de forma lineal en el tamaño del punto haría
> invisible al 99 % de los incendios y dejaría tres o cuatro círculos gigantes. El
> logaritmo comprime la escala y vuelve legible la distribución.

---

## 2. Modelo de datos en Tableau

Las tres fuentes se conectan como **fuentes de datos independientes**, sin relaciones
entre ellas. No hace falta unirlas: cada hoja consume una sola fuente.

```
   hechos_incendios.csv        focos_muestra.csv        resumen_origen.csv
   (fuente principal)          (mapa de puntos)         (tarjetas de KPI)
          │                           │                        │
   Hojas 1-8, 10, 12               Hoja 11              Tarjetas de resumen
```

La coherencia entre las tres está garantizada en el origen: las tres se generan a partir
del mismo Data Lake en la misma ejecución del script.

---

## 3. Estructura del tablero

### Página 1 — «Panorama del origen del fuego»

Responde a la pregunta central: **¿el fuego humano y el natural se comportan igual?**

| Hoja | Tipo de gráfico | Columnas | Filas | Color |
|---|---|---|---|---|
| Eventos por origen | Barras verticales | `Origen del fuego` | `SUM(N incendios)` | `Origen del fuego` |
| Superficie por origen | Barras verticales | `Origen del fuego` | `SUM(Acres)` | `Origen del fuego` |
| Estacionalidad por origen | Líneas | `Mes` | `SUM(N incendios)` | `Origen del fuego` |
| Severidad media por origen | Barras verticales | `Origen del fuego` | `[Acres promedio por incendio]` | `Origen del fuego` |

**Cifras que debe reproducir:**

| Origen | Eventos | % Eventos | Acres | % Acres | Acres/evento |
|---|---:|---:|---:|---:|---:|
| Antrópico | 1.111.469 | 59,11 % | 29.953.119 | 21,37 % | 26,95 |
| No determinado | 490.528 | 26,09 % | 23.145.930 | 16,52 % | 47,19 |
| Natural | 278.468 | 14,81 % | 87.033.501 | 62,11 % | **312,54** |

### Página 2 — «Magnitud, causas y propiedad»

| Hoja | Tipo | Columnas | Filas | Color |
|---|---|---|---|---|
| Pirámide de clases de tamaño | Barras horizontales | `SUM(N incendios)` | `Clase de tamano` | `Clase de tamano` |
| Superficie por clase de tamaño | Barras horizontales | `SUM(Acres)` | `Clase de tamano` | `Clase de tamano` |
| Causas del fuego | Barras horizontales | `SUM(N incendios)` | `Causa` (ordenada desc.) | `Origen del fuego` |
| Sector de propiedad | Barras horizontales | `SUM(Acres)` | `Sector de propiedad` | `Sector de propiedad` |

**Cifras que debe reproducir:**

| Clase | Rango (acres) | Eventos | % Eventos | Acres | % Acres |
|---|---|---:|---:|---:|---:|
| A | 0 – 0,25 | 666.919 | 35,47 % | 79.231 | 0,06 % |
| B | 0,26 – 9,9 | 939.376 | 49,95 % | 2.016.839 | 1,44 % |
| C | 10 – 99,9 | 220.077 | 11,70 % | 6.279.218 | 4,48 % |
| D | 100 – 299 | 28.427 | 1,51 % | 4.599.518 | 3,28 % |
| E | 300 – 999 | 14.107 | 0,75 % | 7.234.844 | 5,16 % |
| F | 1.000 – 4.999 | 7.786 | 0,41 % | 16.587.256 | 11,84 % |
| G | 5.000 o más | 3.773 | **0,20 %** | 103.335.644 | **73,74 %** |

### Página 3 — «Geografía y evolución temporal»

| Hoja | Tipo | Configuración |
|---|---|---|
| Mapa de focos | Mapa de puntos (`focos_muestra`) | Columnas `AVG(Longitud)`, Filas `AVG(Latitud)`, Detalle: identificador de fila, Tamaño `SUM(Peso logaritmico)`, Color `Origen del fuego` |
| Ranking de estados | Barras horizontales | Columnas `SUM(Acres)`, Filas `Estado` ordenado descendente, Color `Region censal` |
| Serie anual por origen | Líneas | Columnas `Anio`, Filas `SUM(N incendios)`, Color `Origen del fuego` |

**Cifras que debe reproducir (cinco estados con más superficie):**

| Estado | Eventos | Acres | Acres/evento |
|---|---:|---:|---:|
| Alaska | 12.843 | 32.233.094 | 2.509,78 |
| Idaho | 36.698 | 13.684.335 | 372,89 |
| California | 189.550 | 12.745.859 | 67,24 |
| Texas | 142.021 | 9.786.218 | 68,91 |
| Nevada | 16.956 | 9.015.855 | 531,72 |

---

## 4. Paleta de colores

La paleta replica exactamente la del aplicativo de Streamlit, de modo que ambos
productos formen un único sistema visual. El color **no es decorativo**: identifica el
origen del fuego.

| Categoría | Color | Código | Significado |
|---|---|---|---|
| Antrópico | Naranja ember | `#F25C05` | Fuego de origen humano |
| Natural | Azul rayo | `#4FA3F7` | Ignición por descarga eléctrica |
| No determinado | Gris ceniza | `#8C8C8C` | Causa no establecida |
| Acento de alerta | Rojo quemado | `#A62103` | Grandes incendios, superficie |
| Acento secundario | Dorado seco | `#F2A03D` | Frecuencias, conteos |
| Fondo | Negro carbón | `#0D0D0D` | — |
| Texto | Blanco humo | `#F2F2F2` | — |

**Para aplicarla:** clic derecho sobre la leyenda de `Origen del fuego` → *Editar
colores* → *Personalizado* → introducir cada código hexadecimal.

---

## 5. Guía de construcción del libro

1. **Conectar la fuente principal.** Tableau → *Conectar* → *Archivo de texto* →
   `extractos/hechos_incendios.csv`. Verificar que el separador sea la coma y que la
   primera fila se lea como encabezado.
2. **Corregir los roles de campo.** Convertir `Anio`, `Mes` y `Orden de clase` en
   dimensiones (clic derecho → *Convertir en dimensión*).
3. **Asignar roles geográficos.** `Estado` → *Rol geográfico* → *Estado/Provincia*.
   `Codigo estado` → *Estado/Provincia* también.
4. **Crear los campos calculados** de [`calculos/campos-calculados.md`](calculos/campos-calculados.md).
   Son ocho y todos son cocientes de sumas.
5. **Construir las doce hojas** según las tablas de la sección 3.
6. **Aplicar la paleta** de la sección 4 a las leyendas de origen y de clase.
7. **Montar los tres tableros** arrastrando las hojas a la disposición indicada
   (tamaño sugerido: 1300 × 850 px, disposición fija).
8. **Añadir filtros globales.** Arrastrar `Anio`, `Region censal` y `Origen del fuego`
   al estante de filtros, mostrar el control y aplicarlo a **todas las hojas que usen
   esta fuente de datos**.
9. **Guardar** como `Origen_del_Fuego_EEUU_1992_2015.twb` en esta carpeta. Al usar rutas
   relativas a `extractos/`, el libro seguirá funcionando para quien clone el
   repositorio.
10. *(Opcional)* Publicar en Tableau Public y añadir el enlace al README principal.

---

## 6. Hallazgos que el tablero debe hacer visibles

1. **La paradoja frecuencia-magnitud.** El origen antrópico produce el 59,11 % de los
   eventos pero solo el 21,37 % de la superficie; el natural, el 14,81 % de los eventos
   y el 62,11 % de la superficie. La severidad media difiere en un factor de **11,6**.

2. **La estacionalidad diferenciada.** El fuego antrópico alcanza su máximo en marzo y
   abril; el natural, en julio y agosto. Son dos curvas con formas distintas, no una
   curva escalada.

3. **La concentración extrema.** La clase G representa el 0,20 % de los eventos y el
   73,74 % de la superficie. Las pirámides de frecuencia y de superficie están
   invertidas.

4. **La disociación geográfica.** Los estados con más incendios (Georgia, Texas, las
   Carolinas) no son los que más superficie pierden (Alaska, Idaho, Nevada).

---

## 7. Reproducción de los extractos

```bash
cd Tableau
python generar_extractos.py
```

El script exige que el Data Lake exista en `../data/`. Al terminar, ejecuta un control
de consistencia que compara sus totales con los del Data Lake; ambos deben coincidir
exactamente.
