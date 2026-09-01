"""
pages/04_FireQuery.py
================================================================================
FIREQUERY — TERMINAL SQL INTERACTIVA Y DICCIONARIO DE DATOS
Origen del fuego: incendios antropicos vs. naturales, EE.UU. 1992-2015.
================================================================================

Esta pagina abre el Data Lake al usuario: permite escribir y ejecutar sentencias
SQL arbitrarias contra el modelo en estrella, e incorpora el diccionario de datos
completo para que esas consultas puedan escribirse sin consultar documentacion
externa.

MEDIDAS DE ESTABILIDAD IMPLEMENTADAS
------------------------------------
  * Limite de 5.000 filas en el resultado mostrado, para no saturar la memoria
    del navegador.
  * Captura de errores: una consulta mal escrita devuelve el mensaje del motor,
    nunca interrumpe la aplicacion.
  * Sin estado acumulado: cada ejecucion reemplaza el resultado anterior.
"""

import streamlit as st
import pandas as pd

from src.query_manager import get_query_manager
from src.stats_logic import ejecutar_consulta_libre

st.set_page_config(page_title="FireQuery", page_icon="🧯", layout="wide")

LIMITE_FILAS = 5_000

st.title("FireQuery")
st.markdown(
    "Terminal analitica sobre el Data Lake de incendios forestales. "
    "Las consultas se ejecutan con **DuckDB** directamente sobre los archivos "
    "Parquet del modelo en estrella."
)

qm = get_query_manager()
if not qm.esta_completo():
    st.error("El Data Lake no esta disponible. Ejecute los scripts de `Base de datos/`.")
    st.stop()


# ==============================================================================
# GUIA DEL ESQUEMA
# ==============================================================================
with st.expander("Guia del esquema en estrella", expanded=True):
    col_hechos, col_dim = st.columns(2)

    with col_hechos:
        st.markdown("""
        **Tablas de hechos** (una fila por incendio, relacion 1:1 entre ambas)

        | Nombre en SQL | Contenido | Filas |
        |---|---|---|
        | `incendios` | Cuando, donde y por que: fechas, coordenadas y llaves foraneas | 1.880.465 |
        | `magnitud` | Cuanto ardio: superficie en acres y hectareas, clase y bandera de gran incendio | 1.880.465 |

        Ambas se unen por `fire_id`.
        """)

    with col_dim:
        st.markdown("""
        **Tablas de dimension** (catalogos)

        | Nombre en SQL | Contenido | Filas |
        |---|---|---|
        | `origen` | Antropico / Natural / No determinado | 3 |
        | `causas` | Las 13 causas estadisticas del NWCG | 13 |
        | `clases` | Clases de tamano A a G | 7 |
        | `propiedad` | Propietario del terreno y sector agregado | 16 |
        | `ubicacion` | Estado, region censal y condado | 2.847 |
        | `calendario` | Mes, estacion y temporada de fuego | 12 |
        """)

    st.markdown("""
    **Relaciones para escribir los JOIN**

    ```
    incendios.fire_id        = magnitud.fire_id          (1:1)
    incendios.cause_id       = causas.cause_id
    causas.origen_id         = origen.origen_id
    incendios.location_id    = ubicacion.location_id
    incendios.owner_id       = propiedad.owner_id
    incendios.discovery_month = calendario.mes
    magnitud.class_id        = clases.class_id
    ```
    """)


# ==============================================================================
# PROTOCOLO DE USO
# ==============================================================================
col_guia, col_limites = st.columns(2)

with col_guia:
    st.markdown("""
    **Como escribir una consulta**

    1. Use los nombres logicos de la tabla anterior (`incendios`, `magnitud`, ...),
       no los nombres de los archivos Parquet.
    2. Especifique las columnas que necesita en lugar de `SELECT *`. El formato
       columnar lee solo las columnas solicitadas, de modo que enumerarlas
       acelera notablemente la consulta.
    3. Para relacionar hechos con dimensiones, utilice siempre las llaves
       indicadas en el bloque de relaciones.
    """)

with col_limites:
    st.markdown(f"""
    **Limites del entorno**

    1. El resultado se trunca a **{LIMITE_FILAS:,} filas**. Si necesita mas,
       agregue en la consulta en lugar de listar.
    2. La terminal no conserva el resultado de consultas anteriores: cada
       ejecucion libera el anterior para no acumular memoria.
    3. El motor es DuckDB, cuyo dialecto SQL es muy cercano al de PostgreSQL:
       admite `QUALIFY`, `USING SAMPLE`, `NTILE`, `FILTER` y listas con `UNNEST`.
    """)

st.markdown("---")


# ==============================================================================
# CONSULTAS DE EJEMPLO
# ==============================================================================
st.subheader("Consultas de ejemplo")

EJEMPLOS = {
    "Superficie por origen":
        "SELECT o.descripcion AS origen,\n"
        "       COUNT(*) AS eventos,\n"
        "       ROUND(SUM(m.superficie_acres), 0) AS acres,\n"
        "       ROUND(AVG(m.superficie_acres), 2) AS media_acres,\n"
        "       ROUND(MEDIAN(m.superficie_acres), 2) AS mediana_acres\n"
        "FROM incendios i\n"
        "JOIN causas   c ON i.cause_id  = c.cause_id\n"
        "JOIN origen   o ON c.origen_id = o.origen_id\n"
        "JOIN magnitud m ON i.fire_id   = m.fire_id\n"
        "GROUP BY o.descripcion\n"
        "ORDER BY acres DESC;",

    "Los 20 incendios mayores":
        "SELECT i.fire_year AS anio,\n"
        "       u.state_name AS estado,\n"
        "       c.descripcion_es AS causa,\n"
        "       ROUND(m.superficie_acres, 0) AS acres,\n"
        "       cl.letra AS clase\n"
        "FROM incendios  i\n"
        "JOIN magnitud   m  ON i.fire_id     = m.fire_id\n"
        "JOIN clases     cl ON m.class_id    = cl.class_id\n"
        "JOIN causas     c  ON i.cause_id    = c.cause_id\n"
        "JOIN ubicacion  u  ON i.location_id = u.location_id\n"
        "ORDER BY m.superficie_acres DESC\n"
        "LIMIT 20;",

    "Estacionalidad por region":
        "SELECT cal.abreviatura AS mes,\n"
        "       u.region_censo AS region,\n"
        "       COUNT(*) AS eventos\n"
        "FROM incendios  i\n"
        "JOIN calendario cal ON i.discovery_month = cal.mes\n"
        "JOIN ubicacion  u   ON i.location_id     = u.location_id\n"
        "GROUP BY cal.mes, cal.abreviatura, u.region_censo\n"
        "ORDER BY cal.mes, eventos DESC;",

    "Perfil de una causa concreta":
        "SELECT u.state_name AS estado,\n"
        "       COUNT(*) AS eventos,\n"
        "       ROUND(SUM(m.superficie_acres), 0) AS acres,\n"
        "       ROUND(AVG(m.superficie_acres), 2) AS media_acres\n"
        "FROM incendios i\n"
        "JOIN causas    c ON i.cause_id    = c.cause_id\n"
        "JOIN magnitud  m ON i.fire_id     = m.fire_id\n"
        "JOIN ubicacion u ON i.location_id = u.location_id\n"
        "WHERE c.descripcion_es = 'Fuegos artificiales'\n"
        "GROUP BY u.state_name\n"
        "ORDER BY eventos DESC\n"
        "LIMIT 15;",
}

# El valor inicial de la terminal se guarda en el estado de sesion para que los
# botones de ejemplo puedan sustituirlo sin perder lo que el usuario escribio.
if "consulta_activa" not in st.session_state:
    st.session_state.consulta_activa = EJEMPLOS["Superficie por origen"]

columnas_botones = st.columns(len(EJEMPLOS))
for columna, (titulo, sentencia) in zip(columnas_botones, EJEMPLOS.items()):
    with columna:
        if st.button(titulo, width="stretch"):
            st.session_state.consulta_activa = sentencia
            st.rerun()


# ==============================================================================
# TERMINAL
# ==============================================================================
st.subheader("Terminal")

consulta_usuario = st.text_area(
    "Sentencia SQL",
    value=st.session_state.consulta_activa,
    height=230,
    label_visibility="collapsed",
)

if st.button("Ejecutar consulta", type="primary"):
    # Se libera el resultado anterior antes de calcular el nuevo.
    st.session_state.pop("resultado_firequery", None)

    with st.spinner("Consultando el Data Lake..."):
        resultado, error = ejecutar_consulta_libre(qm, consulta_usuario)

    if error:
        st.error(f"El motor rechazo la consulta:\n\n```\n{error}\n```")
    elif resultado is None or resultado.empty:
        st.warning("La consulta se ejecuto correctamente pero no devolvio filas.")
    else:
        filas_totales = len(resultado)
        if filas_totales > LIMITE_FILAS:
            st.warning(
                f"La consulta devolvio {filas_totales:,} filas. Se muestran las "
                f"primeras {LIMITE_FILAS:,} por estabilidad del navegador."
            )
            resultado = resultado.head(LIMITE_FILAS)

        st.success(f"Consulta ejecutada: {filas_totales:,} filas devueltas.")
        st.session_state.resultado_firequery = resultado
        st.dataframe(resultado, width="stretch")

st.markdown("---")


# ==============================================================================
# DICCIONARIO DE DATOS
# ==============================================================================
st.header("Diccionario de datos")
st.caption(
    "Descripcion de cada campo del modelo. La documentacion completa, incluida la "
    "trazabilidad con los campos originales de la fuente, se encuentra en "
    "`Base de datos/DICCIONARIO_DE_DATOS.md`."
)

diccionarios = {
    "incendios — tabla de hechos": pd.DataFrame({
        "Campo": ["fire_id", "fod_id", "fire_year", "discovery_date", "discovery_doy",
                  "discovery_month", "discovery_time", "cause_id", "location_id",
                  "owner_id", "latitude", "longitude"],
        "Tipo": ["Entero", "Entero", "Entero", "Fecha", "Entero", "Entero", "Texto",
                 "Entero", "Entero", "Entero", "Real", "Real"],
        "Descripcion": [
            "Llave primaria subrogada, correlativa, asignada por el proceso ETL.",
            "Identificador global del incendio en la fuente original (FOD_ID). Permite trazar cualquier fila hasta la base de Kaggle.",
            "Ano calendario en que el incendio fue detectado o confirmado.",
            "Fecha de deteccion en formato ISO (AAAA-MM-DD), convertida desde el dia juliano de la fuente.",
            "Dia del ano de la deteccion, de 1 a 366.",
            "Mes de la deteccion. Llave foranea hacia la dimension de calendario.",
            "Hora de deteccion en formato HHMM. Ausente en el 46,94% de los registros.",
            "Llave foranea hacia el catalogo de causas NWCG.",
            "Llave foranea hacia la dimension geografica estado-condado.",
            "Llave foranea hacia el catalogo de propiedad del terreno.",
            "Latitud del punto de origen, en grados decimales (datum NAD83).",
            "Longitud del punto de origen, en grados decimales (datum NAD83).",
        ],
    }),
    "magnitud — tabla de hechos": pd.DataFrame({
        "Campo": ["fire_id", "class_id", "superficie_acres", "superficie_ha",
                  "es_gran_incendio"],
        "Tipo": ["Entero", "Entero", "Real", "Real", "Entero"],
        "Descripcion": [
            "Llave primaria y foranea hacia `incendios`. Establece la relacion 1:1.",
            "Llave foranea hacia el catalogo de clases de tamano NWCG.",
            "Superficie final dentro del perimetro del incendio, en acres. Medida principal de la investigacion.",
            "La misma superficie convertida a hectareas (1 acre = 0,40468564224 ha). Campo derivado calculado en el ETL.",
            "Bandera 1/0 que marca los incendios de clase F o G, es decir de 1.000 acres o mas. Campo derivado.",
        ],
    }),
    "origen y causas — dimensiones": pd.DataFrame({
        "Campo": ["origen.origen_id", "origen.descripcion", "origen.naturaleza",
                  "origen.definicion", "causas.cause_id", "causas.descripcion_en",
                  "causas.descripcion_es", "causas.origen_id"],
        "Tipo": ["Entero", "Texto", "Texto", "Texto", "Entero", "Texto", "Texto", "Entero"],
        "Descripcion": [
            "Llave primaria del catalogo de origen (1 a 3).",
            "Categoria de origen: Antropico, Natural o No determinado.",
            "Clasificacion complementaria: Evitable, No evitable o Indeterminada.",
            "Criterio operativo con el que se asigno la categoria.",
            "Codigo original de la causa estadistica NWCG (STAT_CAUSE_CODE, de 1 a 13).",
            "Etiqueta oficial de la causa en ingles, tal como aparece en la fuente.",
            "Traduccion al espanol empleada en la interfaz del aplicativo.",
            "Llave foranea hacia el catalogo de origen. Resuelve la dependencia transitiva causa-origen.",
        ],
    }),
    "clases, propiedad, ubicacion y calendario — dimensiones": pd.DataFrame({
        "Campo": ["clases.letra", "clases.limite_inf", "clases.limite_sup",
                  "propiedad.descripcion", "propiedad.sector",
                  "ubicacion.state_code", "ubicacion.state_name",
                  "ubicacion.region_censo", "ubicacion.county_name",
                  "calendario.nombre_mes", "calendario.estacion",
                  "calendario.temporada_fuego"],
        "Tipo": ["Texto", "Real", "Real", "Texto", "Texto", "Texto", "Texto",
                 "Texto", "Texto", "Texto", "Texto", "Texto"],
        "Descripcion": [
            "Letra de la clase de tamano NWCG, de A a G.",
            "Cota inferior del intervalo de superficie de la clase, en acres.",
            "Cota superior del intervalo. Nulo en la clase G, que no tiene tope.",
            "Propietario o gestor del terreno segun el codigo original OWNER_CODE.",
            "Agregacion propia de la investigacion en seis macrocategorias: Federal, Estatal, Privado, Tribal, Local y No especificado.",
            "Codigo de dos letras del estado.",
            "Nombre completo del estado en espanol.",
            "Region de la Oficina del Censo: Noreste, Medio Oeste, Sur u Oeste.",
            "Etiqueta canonica del condado. El campo COUNTY de la fuente es texto libre "
            "con multiples grafias por condado, de modo que la dimension se normaliza "
            "sobre el par (estado, FIPS) y el nombre es solo una etiqueta.",
            "Nombre del mes en espanol.",
            "Estacion del ano correspondiente al mes.",
            "Clasificacion operativa Baja / Media / Alta, construida por el equipo a partir del volumen mensual observado.",
        ],
    }),
}

for titulo, tabla in diccionarios.items():
    st.subheader(titulo)
    st.dataframe(tabla, width="stretch", hide_index=True)

st.caption(
    "Escuela de Estadistica y Ciencias Actuariales · Universidad Central de Venezuela · "
    "Material academico de la asignatura Computacion II."
)
