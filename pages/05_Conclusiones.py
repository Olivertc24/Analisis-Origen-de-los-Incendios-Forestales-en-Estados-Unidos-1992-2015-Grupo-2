"""
pages/05_Conclusiones.py
================================================================================
CONCLUSIONES DE LA INVESTIGACION
Origen del fuego: incendios antropicos vs. naturales, EE.UU. 1992-2015.
================================================================================

Sintesis de los resultados obtenidos, organizada en cuatro bloques: la
infraestructura de datos construida, los perfiles comparativos de cada origen,
los hallazgos sustantivos y las limitaciones y lineas de continuidad.

Todas las cifras citadas provienen de las consultas ejecutadas en las paginas
anteriores sobre el universo completo de 1.880.465 registros.
"""

import streamlit as st

st.set_page_config(page_title="Conclusiones", page_icon="🏁", layout="wide")

st.title("Conclusiones")
st.caption("Origen del fuego en Estados Unidos · 1992-2015")

# ==============================================================================
# 1. INFRAESTRUCTURA
# ==============================================================================
st.header("1. Sobre la infraestructura de datos construida")

with st.expander("1.1. Normalizacion e integridad referencial", expanded=True):
    st.markdown("""
    La base original se distribuye como una unica tabla desnormalizada de 39 columnas,
    en la que descripciones textuales completas se repiten cientos de miles de veces:
    la cadena `Debris Burning`, por ejemplo, aparece 429.028 veces.

    El proceso de normalizacion produjo un **esquema en estrella en Tercera Forma
    Normal** compuesto por dos tablas de hechos en relacion 1:1 y seis dimensiones.
    El caso mas relevante fue la resolucion de la **dependencia transitiva** entre
    causa y origen: el origen del fuego no depende del incendio sino de su causa, de
    modo que ubicarlo en la dimension `causas` y no en la tabla de hechos es lo que
    exige la 3FN.

    Los siete controles de integridad ejecutados al cierre del ETL —ausencia de
    hechos huerfanos respecto de cada dimension y cumplimiento de la relacion 1:1—
    devolvieron **cero incidencias** sobre los 1.880.465 registros cargados.
    """)

with st.expander("1.2. Eficiencia del Data Lake columnar"):
    st.markdown("""
    La conversion del esquema normalizado a formato **Parquet con compresion ZSTD**
    redujo el volumen de 276 MB a **42,8 MB**, un factor de compresion de
    aproximadamente **6,5 veces**.

    Esa reduccion tuvo una consecuencia practica decisiva para el proyecto: el Data
    Lake completo cabe dentro del repositorio, de modo que el aplicativo es
    **autocontenido**. Quien clone el repositorio puede ejecutarlo sin descargar los
    795 MB de la base original ni depender de un servicio externo de almacenamiento.

    Sobre esos archivos, DuckDB resuelve las agregaciones del tablero en decimas de
    segundo, porque lee unicamente las columnas que cada consulta solicita en lugar
    de recorrer filas completas.
    """)

st.markdown("---")

# ==============================================================================
# 2. PERFILES COMPARATIVOS
# ==============================================================================
st.header("2. Perfiles comparativos por origen del fuego")

st.info("**Universo de referencia:** 1.880.465 incendios y 140,1 millones de acres "
        "quemados (56,7 millones de hectareas) entre 1992 y 2015.")

col_antropico, col_natural = st.columns(2)

with col_antropico:
    st.markdown("### Perfil antropico")
    st.markdown("Causas atribuibles a una actividad humana identificada.")
    st.metric("Eventos", "1.111.469", "59,11% del total")
    st.metric("Superficie quemada", "29,95 M acres", "21,37% del total")
    st.metric("Superficie media", "26,95 acres")
    st.metric("Superficie mediana", "1,00 acre")
    st.markdown("""
    **Rasgos caracteristicos**
    - Domina el **conteo** de eventos pero no la superficie.
    - Ventana estacional **amplia**: 249 dias del ano concentran el 80% de sus eventos.
    - Maximo en primavera (marzo y abril), asociado a la quema de desechos.
    - Predomina en el Sureste del pais y en terrenos privados o de propiedad no especificada.
    """)

with col_natural:
    st.markdown("### Perfil natural")
    st.markdown("Ignicion por descarga electrica atmosferica.")
    st.metric("Eventos", "278.468", "14,81% del total")
    st.metric("Superficie quemada", "87,03 M acres", "62,11% del total")
    st.metric("Superficie media", "312,54 acres")
    st.metric("Superficie mediana", "0,20 acres")
    st.markdown("""
    **Rasgos caracteristicos**
    - Minoritario en conteo pero **dominante en superficie**.
    - Ventana estacional **estrecha**: 91 dias concentran el 80% de sus eventos.
    - Maximo en pleno verano (julio y agosto), ligado a la actividad convectiva.
    - Predomina en el Oeste y en tierras federales, estatales y tribales.
    """)

st.markdown("---")

# ==============================================================================
# 3. HALLAZGOS
# ==============================================================================
st.header("3. Hallazgos principales")

st.subheader("3.1. La paradoja frecuencia-magnitud")
st.markdown("""
El resultado central de la investigacion es que **frecuencia y magnitud apuntan en
direcciones opuestas**. El origen antropico produce cuatro veces mas incendios que
el natural (59,11% frente a 14,81% de los eventos), pero el natural quema casi tres
veces mas superficie (62,11% frente a 21,37% de los acres).

La razon esta en la severidad tipica de cada evento: la superficie media de un
incendio natural (312,54 acres) es **11,6 veces** la de uno antropico (26,95 acres).

La consecuencia para la interpretacion es que la pregunta "¿cual es el principal
problema de incendios de Estados Unidos?" no admite una respuesta unica: depende de
si se mide en numero de eventos o en superficie afectada. Ambas mediciones son
correctas y describen fenomenos distintos.
""")

st.subheader("3.2. La ventana estacional humana es 2,7 veces mas amplia")
st.markdown("""
El fuego natural es un fenomeno **concentrado**: el 80% de sus eventos ocurre en solo
91 dias del ano, el 24,9% del calendario, porque depende de una condicion
meteorologica estacional. El fuego antropico requiere **249 dias** (68,2% del
calendario) para acumular esa misma proporcion.

Este resultado, obtenido de forma independiente en la Consulta 2, coincide con el
hallazgo de Balch y colaboradores (2017): la ignicion humana no solo agrega
incendios al total, sino que **extiende la temporada de fuego** a periodos del ano
en los que el fuego natural es practicamente inexistente. Desde el punto de vista de
la gestion, esto significa que la capacidad de respuesta debe sostenerse durante casi
todo el ano y no solo durante el verano.
""")

st.subheader("3.3. Una concentracion extrema de la superficie")
st.markdown("""
La distribucion de la superficie quemada es de una asimetria excepcional:

- **845 incendios** (el 0,045% de los registros) acumulan el **50%** de toda la
  superficie quemada en 24 anos.
- **6.343 incendios** (el 0,34%) acumulan el **80%**.
- La clase G del NWCG —incendios de 5.000 acres o mas— representa el **0,20%** de
  los eventos y el **73,74%** de la superficie.

Esta concentracion se reproduce **dentro de cada origen por separado**: en los
incendios naturales el cuarto cuartil concentra el 99,93% de la superficie del grupo.
""")

st.warning("""
**Implicacion estadistica.** En una distribucion asi, la media aritmetica de la
superficie quemada (74,52 acres para el universo completo) no describe a ningun
incendio real: la mediana es de **1,00 acre**. Reportar la media sin la mediana, o
sin el coeficiente de asimetria que la acompana, produciria una caracterizacion
falsa del fenomeno. Es el motivo por el cual todas las pantallas de este aplicativo
muestran ambas medidas juntas.
""")

st.subheader("3.4. La geografia separa los dos origenes")
st.markdown("""
El patron territorial es nitido. En los estados del Sureste —Georgia, Texas, las
Carolinas— la causa dominante es la **quema de desechos**, y en Misisipi y Alabama el
**incendio intencional**: son estados de alta frecuencia y baja superficie por evento.
En Florida y Arizona la causa dominante es el **rayo**.

Medido en superficie, en cambio, el ranking cambia por completo y lo encabezan Alaska
(32,2 millones de acres), Idaho, California, Texas y Nevada: estados del Oeste con
grandes extensiones de tierra federal y baja densidad poblacional.

La superficie media de los incendios naturales supera a la de los antropicos en
**todos** los sectores de propiedad, pero la brecha se dispara en tierras tribales
(46,8 veces) y estatales (22,7 veces), donde la lejania y la dificultad de acceso
retrasan la respuesta.
""")

st.markdown("---")

# ==============================================================================
# 4. LIMITACIONES
# ==============================================================================
st.header("4. Limitaciones del estudio")

st.markdown("""
Se declaran explicitamente las siguientes limitaciones, ninguna de las cuales
invalida los resultados pero todas las cuales acotan su alcance:

1. **Causa no determinada en el 26,09% de los registros.** Poco mas de una cuarta
   parte de los incendios no puede asignarse a ningun origen. Esta investigacion
   optó por mantenerlos como categoria propia en lugar de imputarlos, lo que implica
   que las participaciones reportadas para los origenes antropico y natural son
   **cotas inferiores**.

2. **La categoria residual crece con el tiempo.** Su participacion pasa del 23,1% en
   1992 al 32,8% en 2015. Esto refleja un cambio en la practica de registro —mas
   agencias reportantes incorporadas al sistema— y no un cambio en el fenomeno. Por
   ello, las series temporales de composicion por origen no deben leerse como
   tendencias del comportamiento del fuego.

3. **Calidad del campo de condado.** El campo `COUNTY` de la fuente es texto libre y
   no un catalogo controlado: el mismo condado aparece con hasta ocho grafias
   distintas y el 23,2% de los valores son codigos numericos. El ETL saneo esa
   dimension normalizando sobre el par (estado, codigo FIPS), lo que redujo 6.070
   combinaciones espurias a **2.795 condados reales**. Aun asi, el 36,06% de los
   registros no reporta FIPS, de modo que el analisis a escala de condado se apoya en
   menos de dos tercios del universo. Los analisis a escala de estado y de region
   censal no estan afectados.

4. **Naturaleza descriptiva del diseno.** Todas las diferencias reportadas son
   diferencias observadas en el universo. No se realizaron pruebas de significacion
   ni se estimaron relaciones causales.

5. **Sesgo de cobertura de la fuente.** La base incluye unicamente los incendios que
   alguna agencia reporto y que cumplian los criterios minimos de Short (2017). Los
   incendios no reportados, por definicion, no estan.
""")

st.markdown("---")

# ==============================================================================
# 5. RECOMENDACIONES
# ==============================================================================
st.header("5. Lineas de continuidad")

st.markdown("""
Se sugieren a futuros equipos las siguientes extensiones, todas viables sobre el
modelo de datos ya construido:

- **Cruce con densidad poblacional.** Normalizar la frecuencia de incendios
  antropicos por habitantes o por kilometro de carretera permitiria distinguir si la
  concentracion en el Sureste responde a exposicion o a practicas especificas.

- **Analisis de la interfaz urbano-forestal.** Las coordenadas del modelo permiten
  calcular la distancia de cada foco a zonas urbanizadas y contrastar la hipotesis de
  que la proximidad determina el origen.

- **Estudio inferencial de la severidad.** Un modelo que estime la superficie
  esperada en funcion del origen, la clase de propiedad y la estacion excederia el
  nivel descriptivo de este trabajo, pero el modelo de datos ya lo soporta.

- **Extension temporal.** El Forest Service ha publicado ediciones posteriores de la
  FPA FOD que amplian la serie mas alla de 2015. Los scripts de la carpeta
  `Base de datos/` admiten carga incremental sin modificaciones.
""")

st.markdown("---")
st.caption(
    "Escuela de Estadistica y Ciencias Actuariales · Universidad Central de Venezuela · "
    "Material academico de la asignatura Computacion II."
)
