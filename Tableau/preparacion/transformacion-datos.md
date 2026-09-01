# Registro de transformaciones — Preparación de datos para Tableau

Detalle del proceso que convierte el Data Lake Parquet del proyecto en los extractos CSV
que alimentan el tablero. Todo el proceso está implementado en
[`../generar_extractos.py`](../generar_extractos.py) y es reproducible con un comando.

---

## 1. Por qué no se conecta Tableau al dato crudo

Tableau podría conectarse directamente al Data Lake de 1,88 millones de registros. No se
hace, por tres razones:

| Razón | Explicación |
|---|---|
| **Rendimiento** | Cada interacción del usuario (un filtro, un cambio de nivel) reevalúa las consultas. Sobre 1,88 millones de filas eso introduce una latencia perceptible; sobre 245.653 filas agregadas, no. |
| **Portabilidad** | Un CSV se abre en cualquier instalación de Tableau, incluida Tableau Public, sin conectores ni controladores adicionales. Un Parquet requiere un conector específico. |
| **Granularidad suficiente** | El tablero nunca desciende al incendio individual. Su unidad mínima de lectura es la combinación año-mes-estado-causa-clase-sector. Agregar a ese nivel no pierde ninguna información que el tablero necesite. |

---

## 2. Cadena de transformación

```
FPA_FOD_20170508.sqlite (Kaggle, 795 MB, 1 tabla desnormalizada)
        │
        │  [ETL: scripts 01–03 de "Base de datos/"]
        │  Normalización a 3FN · esquema en estrella · verificación de integridad
        ▼
incendios_eeuu_1992_2015.db (276 MB, 8 tablas)
        │
        │  [script 04]  Exportación a formato columnar
        ▼
data/*.parquet (42,7 MB, 8 archivos)
        │
        │  [generar_extractos.py]  Agregación + control de consistencia
        ▼
Tableau/extractos/*.csv (26,6 MB, 3 archivos)
```

---

## 3. Transformaciones aplicadas al generar los extractos

### T1 — Desnormalización controlada

El modelo en estrella se vuelve a aplanar en una única tabla ancha. Es la operación
inversa a la normalización del ETL, y es deliberada: Tableau trabaja mejor con una tabla
única que con un modelo de siete uniones, y el volumen ya no es un problema tras la
agregación.

Se materializan en el extracto los atributos que provienen de las dimensiones:

| Atributo en el extracto | Dimensión de origen |
|---|---|
| `Origen del fuego` | `origen_fuego.descripcion` |
| `Causa` | `causas.descripcion_es` |
| `Clase de tamano`, `Orden de clase` | `clases_tamano` |
| `Sector de propiedad` | `propiedad_terreno.sector` |
| `Estado`, `Codigo estado`, `Region censal` | `ubicacion` |
| `Mes abrev`, `Estacion`, `Temporada de fuego` | `calendario_estacional` |

### T2 — Agregación a sumas y conteos

**La transformación más importante del proceso.** Las medidas del extracto son:

| Medida | Agregación aplicada | Aditiva |
|---|---|---|
| `N incendios` | `COUNT(*)` | Sí |
| `Acres` | `SUM(superficie_acres)` | Sí |
| `Hectareas` | `SUM(superficie_ha)` | Sí |
| `N grandes incendios` | `SUM(es_gran_incendio)` | Sí |

**No se almacena ningún promedio.** Todas las medidas son aditivas, es decir, se pueden
sumar en cualquier nivel sin perder validez. Los promedios se reconstruyen en Tableau
como cocientes de sumas (ver [`../calculos/campos-calculados.md`](../calculos/campos-calculados.md)).

Si el extracto guardara `acres_promedio` por fila, cualquier agregación posterior —por
estado, por año, por origen— produciría un promedio no ponderado y por tanto incorrecto.

### T3 — Recorte de columnas redundantes

Se omiten deliberadamente los atributos descriptivos que duplican información ya
presente en forma corta:

| Columna omitida | Motivo |
|---|---|
| `nombre_mes` | Se conserva `Mes abrev`, suficiente para los ejes |
| `descripcion_en` (causa en inglés) | Se conserva la traducción al español |
| `descripcion` de la clase (rango textual) | Se conserva la letra y su orden |
| `naturaleza` del origen | Derivable del propio origen |
| `propietario` detallado (16 valores) | Se conserva el `Sector` agregado (6 valores) |

Este recorte redujo el archivo de **43,5 MB a 23,6 MB** sin perder ninguna capacidad de
análisis, y además redujo el número de filas de 274.668 a 245.653 al eliminar una
dimensión del grano.

### T4 — Muestreo aleatorio para el mapa de puntos

El mapa de puntos necesita incendios individuales, no agregados. Se extrae una muestra
aleatoria simple de **40.000 registros**, que preserva la forma de la distribución
espacial y se dibuja con fluidez en el navegador.

**Detalle técnico:** se emplea `ORDER BY random() LIMIT n` y no la cláusula
`USING SAMPLE` de DuckDB. El optimizador empuja el muestreo hasta la lectura del archivo,
de modo que la muestra se tomaría **antes** de aplicar las uniones y el resultado
quedaría muy por debajo del tamaño solicitado. El ordenamiento aleatorio con límite se
resuelve mediante una selección de los n mejores y garantiza el tamaño exacto.

> La muestra se usa **únicamente** para el mapa. Todas las métricas del tablero se
> calculan sobre el extracto agregado, que contiene el universo completo.

### T5 — Precálculo de la escala logarítmica

Se añade la columna `Peso logaritmico = LOG10(acres + 1) + 0,15`, destinada al tamaño de
la marca en el mapa. La justificación está en
[`../calculos/campos-calculados.md`](../calculos/campos-calculados.md), campo 9.

---

## 4. Control de consistencia

Al terminar, el script compara los totales del extracto agregado con los del Data Lake.
Resultado de la ejecución de referencia:

| Indicador | Data Lake | Extracto | Estado |
|---|---:|---:|---|
| Incendios | 1.880.465 | 1.880.465 | ✅ |
| Acres quemados | 140.132.549,55 | 140.132.549,55 | ✅ |

**Si este control fallara, el tablero mostraría cifras distintas a las del aplicativo de
Streamlit.** Por eso se ejecuta automáticamente en cada generación y se reporta en la
salida del script.

---

## 5. Nomenclatura de los campos

Los encabezados del CSV se escriben ya con el nombre que tendrán en Tableau: en español,
con mayúscula inicial y sin guiones bajos. Así se evita renombrar 17 campos a mano en la
interfaz, operación tediosa y propensa a errores que además rompería los campos
calculados si se hiciera después de crearlos.

| Campo en el modelo de datos | Encabezado en el extracto |
|---|---|
| `fire_year` | `Anio` |
| `discovery_month` | `Mes` |
| `abreviatura` | `Mes abrev` |
| `state_code` | `Codigo estado` |
| `state_name` | `Estado` |
| `region_censo` | `Region censal` |
| `origen_fuego.descripcion` | `Origen del fuego` |
| `causas.descripcion_es` | `Causa` |
| `clases_tamano.letra` | `Clase de tamano` |
| `clases_tamano.orden` | `Orden de clase` |
| `propiedad_terreno.sector` | `Sector de propiedad` |
| `COUNT(*)` | `N incendios` |
| `SUM(superficie_acres)` | `Acres` |
| `SUM(superficie_ha)` | `Hectareas` |
| `SUM(es_gran_incendio)` | `N grandes incendios` |

> Los nombres se escriben **sin acentos ni eñes**. Los conectores de texto plano de
> Tableau pueden interpretar mal los caracteres no ASCII en los encabezados según la
> configuración regional del equipo, lo que rompería las referencias de los campos
> calculados. Es una precaución de portabilidad, no una limitación del formato.

---

## 6. Ajustes que quedan por hacer dentro de Tableau

El extracto no puede transmitir cierta información semántica; hay que declararla al
conectar:

| Ajuste | Campos afectados | Cómo se hace |
|---|---|---|
| Convertir en dimensión | `Anio`, `Mes`, `Orden de clase` | Clic derecho → *Convertir en dimensión* |
| Asignar rol geográfico | `Estado`, `Codigo estado` | Clic derecho → *Rol geográfico* → *Estado/Provincia* |
| Asignar rol geográfico | `Latitud`, `Longitud` (en `focos_muestra`) | Clic derecho → *Rol geográfico* → *Latitud* / *Longitud* |
| Formato de porcentaje | Campos calculados 3, 4, 5 | Clic derecho → *Formato de números* → *Porcentaje*, 2 decimales |
| Formato de millares | `Acres`, `Hectareas`, `N incendios` | Clic derecho → *Formato de números* → *Número*, separador de miles |

Sin el primer ajuste, Tableau sumaría los años (1992 + 1993 + …) en lugar de agruparlos.
