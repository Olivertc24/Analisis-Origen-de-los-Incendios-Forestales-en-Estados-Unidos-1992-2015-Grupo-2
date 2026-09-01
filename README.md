![Origen del fuego en Estados Unidos](assets/banner_incendios.png)

### ▶ Aplicativo en vivo: **[incendios-eeuu-grupo2.streamlit.app](https://incendios-eeuu-grupo2.streamlit.app)**
### 📊 Tablero en vivo: **[Tableau Public](https://public.tableau.com/app/profile/oliver.triveno/viz/Origen_del_Fuego_EEUU_1992_2015/1_Panoramadelorigen)**

# Origen del fuego en Estados Unidos: perfil comparativo entre incendios antrópicos y naturales (1992–2015)

Investigación estadística descriptiva sobre **1.880.465 incendios forestales
geo-referenciados** ocurridos en Estados Unidos entre 1992 y 2015, que suman **140,1
millones de acres** (56,7 millones de hectáreas) de superficie quemada.

El proyecto separa un fenómeno que suele analizarse como si fuera uno solo: el fuego de
**origen humano** y el de **origen natural**. Son dos procesos con lógicas distintas
—uno ligado a la actividad cotidiana, otro a la meteorología— y por tanto con
comportamientos estadísticos, estacionales y geográficos diferentes.

---

## El hallazgo central

**Frecuencia y magnitud apuntan en direcciones opuestas.**

| | Origen antrópico | Origen natural |
|---|---:|---:|
| Incendios registrados | **1.111.469** (59,11%) | 278.468 (14,81%) |
| Superficie quemada | 29,95 M acres (21,37%) | **87,03 M acres (62,11%)** |
| Superficie media por evento | 26,95 acres | **312,54 acres** |
| Ventana estacional (días que concentran el 80% de sus eventos) | **249 días** | 91 días |

El fuego humano produce **cuatro veces más incendios**; el natural quema **casi tres
veces más superficie**. Y la temporada humana es **2,7 veces más amplia**, porque no
depende de las tormentas eléctricas: se extiende a meses en los que el fuego natural es
prácticamente inexistente.

A ello se suma una concentración extrema: **845 incendios** —el 0,045% de los
registros— acumulan la mitad de toda la superficie quemada en 24 años.

---

## Arquitectura del proyecto

```
                 Kaggle: FPA_FOD_20170508.sqlite  (795 MB, 1 tabla, 39 columnas)
                                  │
                                  ▼
         [ETL por lotes]  Normalización a 3FN · esquema en estrella
                                  │
                                  ▼
                 SQLite normalizado  (276 MB, 8 tablas, 6 dimensiones)
                                  │
                                  ▼
         [Exportación]  Formato columnar Parquet + compresión ZSTD
                                  │
                                  ▼
                    Data Lake  (42,7 MB — versionado en el repositorio)
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
            DuckDB + Streamlit             Tableau Desktop
         (investigación interactiva)      (tablero ejecutivo)
```

### ¿Por qué este conjunto de herramientas?

| Herramienta | Papel en el proyecto | Razón de la elección |
|---|---|---|
| **SQLite** | Motor del esquema normalizado | Sin servidor, portable, con integridad referencial completa. |
| **pandas** | Transformación por lotes en el ETL | Lectura en fragmentos de 150.000 filas: el consumo de memoria no depende del tamaño de la fuente. |
| **Parquet** | Formato del Data Lake | Almacenamiento columnar: reduce el volumen **6,5×** y permite leer solo las columnas que cada consulta necesita. |
| **DuckDB** | Motor analítico del aplicativo | OLAP embebido y vectorizado; consulta los Parquet directamente, sin cargarlos en memoria. |
| **Streamlit** | Aplicativo de la investigación | Publica el análisis completo —metodología, resultados y terminal SQL— en una interfaz navegable. |
| **Tableau** | Tablero ejecutivo | Lectura visual de las métricas macro, complementaria al detalle estadístico del aplicativo. |

---

## Metodología

Investigación de **nivel descriptivo**, diseño **no experimental** y **documental sobre
fuente secundaria**. Al trabajar con el universo completo de registros y no con una
muestra, las medidas calculadas son **parámetros** y no estimadores: no se realizan
pruebas de significación ni inferencias más allá del universo procesado.

### Pregunta de investigación

> ¿Cómo se diferencian los incendios forestales de origen antrópico y los de origen
> natural registrados en Estados Unidos entre 1992 y 2015, en cuanto a su frecuencia,
> su magnitud, su distribución estacional y su localización geográfica?

### Objetivo general

Caracterizar de manera comparativa los incendios forestales de origen antrópico y
natural del período, a partir de su frecuencia, magnitud, estacionalidad y distribución
geográfica, con el fin de construir perfiles diferenciados de ambos tipos de evento.

### Objetivos específicos

1. Normalizar la base original hasta la Tercera Forma Normal mediante un esquema en
   estrella con integridad referencial verificada.
2. Construir la variable *origen del fuego* a partir de la causa estadística NWCG, con
   un criterio de clasificación explícito y reproducible.
3. Transformar el esquema en un Data Lake columnar que haga viable el análisis de 1,88
   millones de registros en un equipo de escritorio.
4. Calcular los estadísticos descriptivos de tendencia central, posición, dispersión y
   forma de la superficie quemada.
5. Describir la distribución estacional y geográfica de cada origen.
6. Desarrollar un aplicativo en Streamlit y un tablero en Tableau que permitan explorar
   la investigación y reproducir sus resultados.

### Universo y unidad de análisis

- **Universo:** los 1.880.465 incendios geo-referenciados ocurridos en los 50 estados,
  el Distrito de Columbia y Puerto Rico entre el 1 de enero de 1992 y el 31 de diciembre
  de 2015 que cumplen los criterios de inclusión de la base FPA FOD.
- **Unidad de análisis:** cada incendio individual registrado (`fire_id`), trazable
  hasta la fuente original mediante `fod_id`.
- **Técnicas:** distribuciones de frecuencias absolutas, relativas y acumuladas; medidas
  de tendencia central, posición, dispersión y forma.

### Criterio de clasificación del origen

| Origen | Causas NWCG que agrupa | Eventos | % |
|---|---|---:|---:|
| **Antrópico** | Quema de desechos, incendio intencional, uso de equipos, fogata, menores, fumadores, ferrocarril, línea eléctrica, fuegos artificiales, estructural | 1.111.469 | 59,11% |
| **Natural** | Rayo | 278.468 | 14,81% |
| **No determinado** | Miscelánea, ausente/no definida | 490.528 | 26,09% |

> La literatura suele reportar ~84% de origen humano. Esa cifra asigna *Miscelánea* al
> bloque humano y excluye del denominador los registros *Ausente/No definida*. Aplicando
> ese mismo criterio sobre este modelo se obtiene **83,75%**, plenamente consistente. El
> presente estudio adopta un criterio más conservador porque imputar la causa de un
> cuarto del universo no corresponde a un diseño descriptivo.

---

## Estructura del repositorio

```
├── app.py                          Tablero principal de la investigación
├── requirements.txt
├── .streamlit/config.toml          Tema visual "Ember"
│
├── Base de datos/
│   ├── 01_creacion_esquema.py      Esquema en estrella + índices
│   ├── 02_poblacion_catalogos.py   Catálogos NWCG y variable de origen
│   ├── 03_procesamiento_carga.py   ETL por lotes + verificación de integridad
│   ├── 04_exportacion_parquet.py   Generación del Data Lake
│   ├── MODELADO_DE_DATOS.md        Diseño del modelo y decisiones justificadas
│   └── DICCIONARIO_DE_DATOS.md     Diccionario campo por campo
│
├── data/                           Data Lake Parquet (8 archivos, 42,7 MB)
│
├── src/
│   ├── query_manager.py            Motor DuckDB sobre el Data Lake
│   └── stats_logic.py              Toda la lógica estadística del proyecto
│
├── pages/
│   ├── 01_Marco_Metodologico.py    Problema, objetivos, operacionalización
│   ├── 02_Marco_Teorico.py         Antecedentes, contexto histórico, fundamentos
│   ├── 03_Cuestionario_SQL.py      Seis consultas analíticas resueltas
│   ├── 04_FireQuery.py             Terminal SQL + diccionario de datos
│   ├── 05_Conclusiones.py          Resultados, limitaciones y continuidad
│   └── 06_Bibliografia.py          Referencias
│
└── Tableau/
    ├── README.md                   Documentación del tablero
    ├── extractos/                  Fuentes de datos del tablero (CSV)
    ├── preparacion/                Transformaciones aplicadas
    └── calculos/                   Campos calculados y su fórmula
```

---

## Puesta en marcha

### 1. Clonar el repositorio

```bash
git clone https://github.com/Olivertc24/Analisis-Origen-de-los-Incendios-Forestales-en-Estados-Unidos-1992-2015-Grupo-2.git
cd Analisis-Origen-de-los-Incendios-Forestales-en-Estados-Unidos-1992-2015-Grupo-2
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Ejecutar el aplicativo

```bash
streamlit run app.py
```

El Data Lake viene incluido en el repositorio, de modo que **el aplicativo funciona sin
descargar nada más**.

### Aplicativo publicado

El aplicativo está desplegado en Streamlit Community Cloud y accesible sin instalar
nada:

**https://incendios-eeuu-grupo2.streamlit.app**

Se actualiza solo: cada `push` a la rama `main` vuelve a construir la aplicación. Los
detalles del despliegue y los pasos para publicar el tablero de Tableau están en la
[guía de despliegue](DESPLIEGUE.md).

Las dependencias se verificaron instalando `requirements.txt` en un entorno limpio y
ejecutando las siete páginas del aplicativo sin errores.

### 4. (Opcional) Reconstruir la base desde cero

Solo si desea reproducir el proceso completo. Requiere descargar
[la base original de Kaggle](https://www.kaggle.com/datasets/rtatman/188-million-us-wildfires)
(795 MB) y colocarla en la carpeta padre del repositorio:

```bash
cd "Base de datos"
python 01_creacion_esquema.py
python 02_poblacion_catalogos.py
python 03_procesamiento_carga.py
python 04_exportacion_parquet.py
```

Tiempo total de referencia: **menos de 30 segundos**. Para indicar otra ubicación de la
base cruda, use la variable de entorno `FPA_FOD_PATH`.

---

---

## Estado del tablero de Tableau

Los **extractos de datos están generados y validados** contra el Data Lake (el script
`Tableau/generar_extractos.py` verifica que los totales coincidan exactamente con los del
aplicativo), y la especificación del tablero está documentada hoja por hoja en
[`Tableau/README.md`](Tableau/README.md), con los campos calculados en
[`Tableau/calculos/campos-calculados.md`](Tableau/calculos/campos-calculados.md) y el
registro de transformaciones en
[`Tableau/preparacion/transformacion-datos.md`](Tableau/preparacion/transformacion-datos.md).

Falta armar el libro `.twb` en Tableau Desktop siguiendo la guía de construcción de la
sección correspondiente. Todas las cifras que cada hoja debe reproducir están tabuladas
en esa documentación, de modo que el resultado es verificable.

---

## Fuente de datos

**1.88 Million US Wildfires** · Licencia **CC0 (dominio público)**
https://www.kaggle.com/datasets/rtatman/188-million-us-wildfires

Cita obligatoria exigida por la documentación de la fuente:

> Short, K. C. (2017). *Spatial wildfire occurrence data for the United States,
> 1992-2015 [FPA_FOD_20170508]* (4.ª ed.). Fort Collins, CO: Forest Service Research
> Data Archive. https://doi.org/10.2737/RDS-2013-0009.4

---

## Créditos

Material académico elaborado para los estudiantes de la **Escuela de Estadística y
Ciencias Actuariales** de la Universidad Central de Venezuela, asignatura
**Computación II**.
