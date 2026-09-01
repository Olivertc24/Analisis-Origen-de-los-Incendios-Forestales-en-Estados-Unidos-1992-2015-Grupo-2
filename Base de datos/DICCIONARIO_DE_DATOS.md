# Diccionario de datos

Modelo **`incendios_eeuu_1992_2015`** — Investigación sobre el origen del fuego en
Estados Unidos, 1992-2015.

Cada campo se documenta con su tipo, su origen en la fuente cruda, su dominio de
valores y las observaciones de calidad detectadas durante el ETL.

**Convención de la columna "Origen":**
- `FUENTE` — el campo proviene directamente de la tabla `Fires` de la base de Kaggle.
- `DERIVADO` — calculado por el ETL a partir de uno o más campos de la fuente.
- `CONSTRUIDO` — clasificación elaborada por el equipo investigador; no existe en la fuente.

---

## Tabla de hechos: `registro_incendios`

**Granularidad:** un registro por incendio detectado. **Filas:** 1.880.465.

| Campo | Tipo | Origen | Campo fuente | Descripción | Nulos |
|---|---|---|---|---|---:|
| `fire_id` | INTEGER PK | DERIVADO | — | Llave primaria subrogada, correlativa, asignada por el ETL. Independiza el modelo de la numeración de la fuente. | 0% |
| `fod_id` | INTEGER | FUENTE | `FOD_ID` | Identificador global único del incendio en la FPA FOD. Garantiza la trazabilidad de cualquier fila hasta el registro original. | 0% |
| `fire_year` | INTEGER | FUENTE | `FIRE_YEAR` | Año calendario en que el incendio fue descubierto o confirmado. Dominio: 1992–2015. | 0% |
| `discovery_date` | DATE | DERIVADO | `DISCOVERY_DATE` | Fecha de detección en formato ISO (`AAAA-MM-DD`). La fuente la almacena como Día Juliano en coma flotante; la conversión se realiza con `date()`. | 0% |
| `discovery_doy` | INTEGER | FUENTE | `DISCOVERY_DOY` | Día del año de la detección. Dominio: 1–366. | 0% |
| `discovery_month` | INTEGER FK | DERIVADO | `DISCOVERY_DATE` | Mes de la detección. Llave foránea hacia `calendario_estacional.mes`. Dominio: 1–12. | 0% |
| `discovery_time` | TEXT | FUENTE | `DISCOVERY_TIME` | Hora de detección en formato `HHMM`. **No interviene en ninguna medida reportada**; se conserva por completitud. | **46,94%** |
| `cause_id` | INTEGER FK | FUENTE | `STAT_CAUSE_CODE` | Llave foránea hacia `causas`. Convertido de `float64` a entero. Dominio: 1–13. | 0% |
| `location_id` | INTEGER FK | DERIVADO | `STATE`, `COUNTY` | Llave foránea hacia `ubicacion`. Resultado de normalizar la combinación estado-condado. | 0% |
| `owner_id` | INTEGER FK | FUENTE | `OWNER_CODE` | Llave foránea hacia `propiedad_terreno`. Convertido a entero. Dominio: 0–15. | 0% |
| `latitude` | REAL | FUENTE | `LATITUDE` | Latitud del punto de origen en grados decimales. Datum NAD83. | 0% |
| `longitude` | REAL | FUENTE | `LONGITUDE` | Longitud del punto de origen en grados decimales. Datum NAD83. | 0% |

---

## Tabla de hechos: `magnitud_incendio`

**Granularidad:** un registro por incendio, relación **1:1** con `registro_incendios`.
**Filas:** 1.880.465.

| Campo | Tipo | Origen | Campo fuente | Descripción | Nulos |
|---|---|---|---|---|---:|
| `fire_id` | INTEGER PK/FK | DERIVADO | — | Llave primaria y foránea hacia `registro_incendios`. Materializa la relación 1:1. | 0% |
| `class_id` | INTEGER FK | FUENTE | `FIRE_SIZE_CLASS` | Llave foránea hacia `clases_tamano`. La letra A–G se traduce a su identificador 1–7. | 0% |
| `superficie_acres` | REAL | FUENTE | `FIRE_SIZE` | **Medida principal de la investigación.** Superficie final dentro del perímetro del incendio, en acres. Rango observado: 0,00009 – 606.945. | 0% |
| `superficie_ha` | REAL | DERIVADO | `FIRE_SIZE` | La misma superficie en hectáreas. Factor: 1 acre = 0,40468564224 ha. | 0% |
| `es_gran_incendio` | INTEGER | DERIVADO | `FIRE_SIZE_CLASS` | Bandera 1/0. Vale 1 si la clase es F o G, es decir 1.000 acres o más. Total en el universo: 11.559 eventos. | 0% |

---

## Dimensión: `origen_fuego`

**La variable segmentadora de la investigación.** No existe en la fuente: es una
construcción del equipo. **Filas:** 3.

| Campo | Tipo | Descripción |
|---|---|---|
| `origen_id` | INTEGER PK | Identificador de la categoría. Dominio: 1–3. |
| `descripcion` | TEXT | `Antropico`, `Natural` o `No determinado`. |
| `naturaleza` | TEXT | `Evitable`, `No evitable` o `Indeterminada`. |
| `definicion` | TEXT | Criterio operativo con el que se asignó la categoría. |

### Contenido y criterio de clasificación

| id | Descripción | Naturaleza | Criterio | Causas que agrupa | Eventos | % |
|---:|---|---|---|---|---:|---:|
| 1 | Antropico | Evitable | Actividad humana identificada en el reporte | 10 causas | 1.111.469 | 59,11% |
| 2 | Natural | No evitable | Ignición por descarga eléctrica atmosférica | 1 causa (`Lightning`) | 278.468 | 14,81% |
| 3 | No determinado | Indeterminada | Causa no establecida o registrada como miscelánea | 2 causas | 490.528 | 26,09% |

> **Nota metodológica.** Las categorías `Miscellaneous` y `Missing/Undefined` se
> mantienen como una tercera categoría en lugar de repartirse entre las anteriores.
> Imputarlas al origen humano —criterio que sí adoptan otros trabajos— elevaría la
> participación antrópica al 83,75%, cifra consistente con la literatura pero que
> supone una atribución no verificable.

---

## Dimensión: `causas`

Catálogo normativo del **National Wildfire Coordinating Group**. **Filas:** 13.

| Campo | Tipo | Origen | Descripción |
|---|---|---|---|
| `cause_id` | INTEGER PK | FUENTE | Código original `STAT_CAUSE_CODE`. Dominio: 1–13. |
| `descripcion_en` | TEXT | FUENTE | Etiqueta oficial en inglés (`STAT_CAUSE_DESCR`). |
| `descripcion_es` | TEXT | CONSTRUIDO | Traducción al español empleada en la interfaz. |
| `origen_id` | INTEGER FK | CONSTRUIDO | Llave foránea hacia `origen_fuego`. **Resuelve la dependencia transitiva causa → origen.** |

### Contenido completo

| id | Etiqueta original | Traducción | Origen | Eventos | Acres quemados |
|---:|---|---|---|---:|---:|
| 5 | Debris Burning | Quema de desechos | Antropico | 429.028 | 5.975.793 |
| 9 | Miscellaneous | Miscelánea | No determinado | 323.805 | 14.394.204 |
| 7 | Arson | Incendio intencional | Antropico | 281.455 | 9.487.274 |
| 1 | Lightning | Rayo | **Natural** | 278.468 | **87.033.501** |
| 13 | Missing/Undefined | Ausente / No definida | No determinado | 166.723 | 8.751.725 |
| 2 | Equipment Use | Uso de equipos | Antropico | 147.612 | 6.799.046 |
| 4 | Campfire | Fogata | Antropico | 76.139 | 3.429.061 |
| 8 | Children | Menores de edad | Antropico | 61.167 | 469.830 |
| 3 | Smoking | Fumadores | Antropico | 52.869 | 842.661 |
| 6 | Railroad | Ferrocarril | Antropico | 33.455 | 849.614 |
| 11 | Powerline | Línea eléctrica | Antropico | 14.448 | 1.609.443 |
| 10 | Fireworks | Fuegos artificiales | Antropico | 11.500 | 318.207 |
| 12 | Structure | Incendio estructural | Antropico | 3.796 | 172.189 |

---

## Dimensión: `clases_tamano`

Escala normativa NWCG, medida en acres. **Filas:** 7.

| Campo | Tipo | Descripción |
|---|---|---|
| `class_id` | INTEGER PK | Identificador. Dominio: 1–7. |
| `letra` | TEXT | Letra de la clase: A–G. |
| `limite_inf` | REAL | Cota inferior del intervalo, en acres. |
| `limite_sup` | REAL | Cota superior. **Nulo en la clase G**, que no tiene tope. |
| `descripcion` | TEXT | Descripción del intervalo en lenguaje natural. |
| `orden` | INTEGER | Secuencia de presentación en gráficos y tablas (1–7). |

### Contenido y distribución observada

| Clase | Intervalo (acres) | Eventos | % Eventos | Acres | % Acres |
|---|---|---:|---:|---:|---:|
| A | 0 – 0,25 | 666.919 | 35,47% | 79.231 | 0,06% |
| B | 0,26 – 9,9 | 939.376 | 49,95% | 2.016.839 | 1,44% |
| C | 10,0 – 99,9 | 220.077 | 11,70% | 6.279.218 | 4,48% |
| D | 100 – 299 | 28.427 | 1,51% | 4.599.518 | 3,28% |
| E | 300 – 999 | 14.107 | 0,75% | 7.234.844 | 5,16% |
| F | 1.000 – 4.999 | 7.786 | 0,41% | 16.587.256 | 11,84% |
| G | 5.000 o más | 3.773 | **0,20%** | 103.335.644 | **73,74%** |

---

## Dimensión: `propiedad_terreno`

Propietario o gestor del terreno en el punto de origen. **Filas:** 16.

| Campo | Tipo | Origen | Descripción |
|---|---|---|---|
| `owner_id` | INTEGER PK | FUENTE | Código original `OWNER_CODE`. Dominio: 0–15. |
| `descripcion` | TEXT | FUENTE | Etiqueta original `OWNER_DESCR`. |
| `sector` | TEXT | **CONSTRUIDO** | Agregación del equipo en seis macrocategorías. |

### Correspondencia código → sector

| Código | Descripción original | Sector asignado | Eventos |
|---:|---|---|---:|
| 14 | MISSING/NOT SPECIFIED | No especificado | 1.050.835 |
| 8 | PRIVATE | Privado | 314.822 |
| 5 | USFS | Federal | 188.338 |
| 2 | BIA | Federal | 106.819 |
| 13 | STATE OR PRIVATE | Mixto estatal-privado | 71.881 |
| 1 | BLM | Federal | 63.278 |
| 7 | STATE | Estatal | 30.790 |
| 3 | NPS | Federal | 17.524 |
| 4 | FWS | Federal | 12.191 |
| 9 | TRIBAL | Tribal | 8.952 |
| 6 | OTHER FEDERAL | Federal | 6.452 |
| 12 | MUNICIPAL/LOCAL | Local | 4.236 |
| 15 | UNDEFINED FEDERAL | Federal | 2.206 |
| 11 | COUNTY | Local | 1.841 |
| 10 | BOR | Federal | 285 |
| 0 | FOREIGN | Extranjero | 15 |

---

## Dimensión: `ubicacion`

Geografía a nivel estado-condado. **Filas:** 2.847 (2.795 condados identificados por FIPS + 52 entradas de estado para los registros sin FIPS).

**Clave natural: `(state_code, fips_code)`.** Véase la observación de calidad al final de la sección.

| Campo | Tipo | Origen | Descripción | Nulos |
|---|---|---|---|---:|
| `location_id` | INTEGER PK | DERIVADO | Llave subrogada autoincremental. | 0% |
| `state_code` | TEXT | FUENTE | Código de dos letras (`STATE`). Dominio: 52 valores (50 estados + DC + PR). | 0% |
| `state_name` | TEXT | CONSTRUIDO | Nombre completo del estado en español. | 0% |
| `region_censo` | TEXT | **CONSTRUIDO** | Región de la Oficina del Censo: `Noreste`, `Medio Oeste`, `Sur`, `Oeste`. | 0% |
| `county_name` | TEXT | DERIVADO | **Etiqueta de presentación**, no identificador. Grafía canónica del condado elegida a partir de todas las observadas en la fuente. | 2,5% |
| `fips_code` | TEXT | FUENTE | Código FIPS de tres dígitos (`FIPS_CODE`). **Identifica al condado dentro del estado**; forma la clave natural junto con `state_code`. | 1,8% |

> **Observación de calidad: el campo `COUNTY` es texto libre.**
>
> Durante el perfilado se detectó que la columna `COUNTY` de la fuente **no es un
> catálogo controlado**. El mismo condado aparece escrito de múltiples formas y, en el
> 23,2% de los casos, el valor no es un nombre sino un código numérico. Ejemplo real
> del par Kansas–FIPS 149, con ocho grafías para un único condado:
>
> `149` · `POTTAWATOMI` · `POTTAWATOMIE` · `Potawatomi` · `Potawatomi Cnty, KS` ·
> `Potawatomi Co, KS` · `Pottawatomie County` · `Pottawatomie`
>
> Normalizar la dimensión sobre ese campo habría producido **6.070 entradas** para un
> país que tiene alrededor de 3.100 condados, con el mismo condado contado varias
> veces y, por tanto, con todas las frecuencias a escala de condado mal calculadas.
>
> **Solución aplicada.** La clave natural de la dimensión es el par
> `(state_code, fips_code)`, que sí es estable. El nombre del condado se degrada a
> etiqueta de presentación: para cada par se elige la grafía alfabética más frecuente
> y se normaliza su capitalización (`POTTAWATOMIE` → `Pottawatomie`). El resultado son
> **2.795 condados reales**.
>
> **Registros sin FIPS.** El 36,06% de los registros de la fuente no reporta ni condado
> ni código FIPS. Estos incendios **se conservan**, agrupados en una entrada por estado
> con `county_name` y `fips_code` nulos, porque el estado consta en el 100% de los
> casos y la unidad de análisis es el incendio. En consecuencia, todo análisis a escala
> de condado se apoya en menos de dos tercios del universo; los análisis a escala de
> estado y de región censal no están afectados.

---

## Dimensión: `calendario_estacional`

Atributos estacionales del mes de detección. **Filas:** 12.

| Campo | Tipo | Origen | Descripción |
|---|---|---|---|
| `mes` | INTEGER PK | DERIVADO | Número de mes. Dominio: 1–12. |
| `nombre_mes` | TEXT | CONSTRUIDO | Nombre del mes en español. |
| `abreviatura` | TEXT | CONSTRUIDO | Abreviatura de tres letras para ejes de gráficos. |
| `estacion` | TEXT | CONSTRUIDO | `Invierno`, `Primavera`, `Verano` u `Otoño`. |
| `temporada_fuego` | TEXT | **CONSTRUIDO** | Clasificación operativa `Baja` / `Media` / `Alta`, derivada del volumen mensual observado en la propia base. |

### Contenido

| Mes | Nombre | Abrev. | Estación | Temporada de fuego |
|---:|---|---|---|---|
| 1 | Enero | Ene | Invierno | Baja |
| 2 | Febrero | Feb | Invierno | Media |
| 3 | Marzo | Mar | Primavera | **Alta** |
| 4 | Abril | Abr | Primavera | **Alta** |
| 5 | Mayo | May | Primavera | Media |
| 6 | Junio | Jun | Verano | Media |
| 7 | Julio | Jul | Verano | **Alta** |
| 8 | Agosto | Ago | Verano | **Alta** |
| 9 | Septiembre | Sep | Otoño | Media |
| 10 | Octubre | Oct | Otoño | Media |
| 11 | Noviembre | Nov | Otoño | Baja |
| 12 | Diciembre | Dic | Invierno | Baja |

---

## Campos de la fuente descartados y su motivo

De las 39 columnas de la tabla `Fires`, 22 no se incorporaron al modelo:

| Campo descartado | Motivo |
|---|---|
| `OBJECTID` | Identificador interno de SpatiaLite, sin valor analítico. |
| `FPA_ID`, `LOCAL_FIRE_REPORT_ID`, `LOCAL_INCIDENT_ID` | Identificadores administrativos internos de cada sistema reportante. La trazabilidad ya está garantizada por `FOD_ID`. |
| `SOURCE_SYSTEM`, `SOURCE_SYSTEM_TYPE` | Metadato del sistema de reporte, ajeno al objeto de esta investigación. |
| `NWCG_REPORTING_AGENCY`, `NWCG_REPORTING_UNIT_ID`, `NWCG_REPORTING_UNIT_NAME` | Dimensión organizativa; no interviene en el estudio del origen del fuego. |
| `SOURCE_REPORTING_UNIT`, `SOURCE_REPORTING_UNIT_NAME` | Ídem. |
| `FIRE_CODE`, `FIRE_NAME`, `COMPLEX_NAME` | Identificación nominal del incidente. `FIRE_NAME` es nulo en el 50,90% de los casos. |
| `ICS_209_INCIDENT_NUMBER`, `ICS_209_NAME`, `MTBS_ID`, `MTBS_FIRE_NAME` | Referencias cruzadas a otros sistemas de información, mayoritariamente nulas. |
| `CONT_DATE`, `CONT_DOY`, `CONT_TIME` | Datos de contención. Nulos en el 47,41% de los casos y **ajenos al objeto de este estudio**. |
| `STAT_CAUSE_DESCR` | Redundante: la descripción vive ahora en la dimensión `causas`. |
| `OWNER_DESCR` | Redundante: reside en `propiedad_terreno`. |
| `FIPS_NAME` | Redundante con `COUNTY`; comparte además su problema de texto libre. |
| `Shape` | Geometría SpatiaLite. Las coordenadas ya se conservan como latitud y longitud. |

---

## Resumen de calidad del dato

| Indicador | Valor |
|---|---:|
| Registros en la fuente | 1.880.465 |
| Registros cargados al modelo | 1.880.465 (100%) |
| Registros descartados por superficie no válida | 0 |
| Campos con nulos en el modelo | 2 (`discovery_time`, `county_name`) |
| Violaciones de integridad referencial detectadas | 0 |
| Condados reales identificados por FIPS | 2.795 |
| Entradas de estado para registros sin FIPS | 52 |
| Grafías distintas de condado colapsadas por el saneamiento | 3.223 |
