"""
pages/03_Cuestionario_SQL.py
================================================================================
CUESTIONARIO SQL — SEIS CONSULTAS ANALITICAS RESUELTAS
Origen del fuego: incendios antropicos vs. naturales, EE.UU. 1992-2015.
================================================================================

Cada apartado presenta el enunciado del problema, la consulta SQL que lo
resuelve, el resultado ejecutado en vivo sobre el Data Lake y la interpretacion
estadistica del hallazgo.

Las consultas se ejecutan contra DuckDB y se apoyan deliberadamente en funciones
de ventana (SUM OVER, RANK, LAG, NTILE, ROW_NUMBER), que permiten resolver en una
sola pasada problemas que de otro modo exigirian varias consultas encadenadas o
procesamiento posterior en Python.
"""

import streamlit as st
import plotly.express as px

from src.query_manager import get_query_manager

st.set_page_config(page_title="Cuestionario SQL", page_icon="🧮", layout="wide")

st.title("Cuestionario SQL")
st.caption(
    "Seis problemas analiticos resueltos sobre el Data Lake de 1.880.465 incendios"
)

qm = get_query_manager()
if not qm.esta_completo():
    st.error("El Data Lake no esta disponible. Ejecute los scripts de `Base de datos/`.")
    st.stop()


def presentar(numero, titulo, enunciado, tecnica, sql, interpretacion, grafico=None):
    """
    Renderiza un apartado completo del cuestionario.

    Centralizar la presentacion evita repetir seis veces la misma estructura y
    garantiza que todos los apartados se lean de forma homogenea.
    """
    st.header(f"Consulta {numero}. {titulo}")

    st.markdown(f"**Enunciado.** {enunciado}")
    st.caption(f"Tecnica SQL empleada: {tecnica}")

    with st.expander("Ver sentencia SQL"):
        st.code(sql, language="sql")

    resultado = qm.execute_query(sql)

    if isinstance(resultado, str):
        st.error(resultado)
        return

    if resultado.empty:
        st.warning("La consulta no devolvio registros.")
        return

    col_tabla, col_grafico = st.columns([1, 1]) if grafico else (st.container(), None)

    with col_tabla:
        st.dataframe(resultado, width="stretch", hide_index=True)

    if grafico:
        with col_grafico:
            st.plotly_chart(grafico(resultado), width="stretch")

    st.success(f"**Interpretacion.** {interpretacion}")
    st.markdown("---")


# ==============================================================================
# CONSULTA 1 — CONCENTRACION DE LA SUPERFICIE QUEMADA
# ==============================================================================
SQL_1 = """
WITH ordenados AS (
    SELECT
        m.superficie_acres,
        -- Suma acumulada de superficie, recorriendo los incendios del mayor al menor
        SUM(m.superficie_acres) OVER (
            ORDER BY m.superficie_acres DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS acres_acumulados,
        ROW_NUMBER() OVER (ORDER BY m.superficie_acres DESC) AS posicion
    FROM magnitud m
),
totales AS (
    SELECT SUM(superficie_acres) AS acres_totales, COUNT(*) AS n_total FROM magnitud
),
umbrales AS (SELECT UNNEST([50, 80, 90, 95]) AS umbral)
SELECT
    umbral                                                      AS "Umbral (% de superficie)",
    MIN(posicion)                                               AS "Incendios necesarios",
    ROUND(MIN(posicion) * 100.0 / (SELECT n_total FROM totales), 4)
                                                                AS "% del total de incendios"
FROM ordenados, umbrales, totales
WHERE acres_acumulados >= umbral / 100.0 * acres_totales
GROUP BY umbral
ORDER BY umbral;
"""

presentar(
    1,
    "Concentracion de la superficie quemada",
    "Ordene todos los incendios de mayor a menor superficie y determine cuantos "
    "hacen falta para acumular el 50%, el 80%, el 90% y el 95% de la superficie "
    "total quemada en el periodo. Exprese esa cantidad tambien como porcentaje del "
    "total de incendios registrados.",
    "Suma acumulada con marco de ventana explicito (`ROWS BETWEEN UNBOUNDED "
    "PRECEDING AND CURRENT ROW`), numeracion de filas y generacion de umbrales con "
    "`UNNEST`.",
    SQL_1,
    "El resultado describe una concentracion extrema. Bastan **845 incendios** "
    "—el 0,045% de los registros— para acumular la mitad de toda la superficie "
    "quemada en 24 anos, y **6.343 incendios** (0,34%) para acumular el 80%. "
    "Dicho de otro modo: 99,66 de cada 100 incendios registrados explican, en "
    "conjunto, apenas la quinta parte de la superficie afectada. Esta es la razon "
    "estadistica por la cual la media aritmetica de la superficie quemada "
    "(74,52 acres) resulta un descriptor enganoso frente a la mediana (1,00 acre): "
    "la media esta enteramente determinada por una cola derecha minuscula en "
    "numero pero dominante en magnitud.",
)


# ==============================================================================
# CONSULTA 2 — AMPLITUD DE LA VENTANA ESTACIONAL
# ==============================================================================
SQL_2 = """
WITH por_dia AS (
    SELECT
        o.descripcion       AS origen,
        i.discovery_doy     AS dia_juliano,
        COUNT(*)            AS eventos
    FROM incendios i
    JOIN causas c ON i.cause_id  = c.cause_id
    JOIN origen o ON c.origen_id = o.origen_id
    GROUP BY o.descripcion, i.discovery_doy
),
acumulado AS (
    SELECT
        origen,
        eventos,
        -- Se recorren los dias del ano del mas activo al menos activo
        SUM(eventos) OVER (
            PARTITION BY origen ORDER BY eventos DESC
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS eventos_acumulados,
        SUM(eventos) OVER (PARTITION BY origen)              AS eventos_del_origen,
        ROW_NUMBER() OVER (PARTITION BY origen ORDER BY eventos DESC) AS dias_necesarios
    FROM por_dia
)
SELECT
    origen                                              AS "Origen del fuego",
    MIN(dias_necesarios)                                AS "Dias que concentran el 80%",
    ROUND(MIN(dias_necesarios) * 100.0 / 365, 1)        AS "% del calendario anual"
FROM acumulado
WHERE eventos_acumulados >= 0.80 * eventos_del_origen
GROUP BY origen
ORDER BY 2;
"""


def grafico_2(df):
    figura = px.bar(
        df, x="Origen del fuego", y="Dias que concentran el 80%",
        color="Origen del fuego",
        color_discrete_map={"Antropico": "#F25C05", "Natural": "#4FA3F7",
                            "No determinado": "#8C8C8C"},
        title="Amplitud de la ventana estacional (dias del ano)",
        text="Dias que concentran el 80%",
    )
    figura.update_layout(template="plotly_dark", showlegend=False, height=380)
    return figura


presentar(
    2,
    "Amplitud de la ventana estacional segun el origen",
    "Para cada origen del fuego, determine en cuantos dias distintos del ano se "
    "concentra el 80% de sus eventos. Ordene los dias del calendario del mas activo "
    "al menos activo y acumule hasta alcanzar ese umbral.",
    "Doble funcion de ventana particionada por origen: suma acumulada sobre un "
    "orden de actividad y total por particion, mas `ROW_NUMBER` para contar dias.",
    SQL_2,
    "El fuego de origen natural concentra el 80% de sus eventos en apenas "
    "**91 dias** del ano, es decir en el 24,9% del calendario: es un fenomeno "
    "acotado a la ventana de tormentas electricas estivales. El fuego de origen "
    "antropico necesita **249 dias** (68,2% del calendario) para acumular esa misma "
    "proporcion. La ventana humana es, por tanto, **2,7 veces mas amplia** que la "
    "natural. Este resultado reproduce de forma independiente el hallazgo central de "
    "Balch y colaboradores (2017): la ignicion humana no solo agrega incendios, sino "
    "que extiende la temporada de fuego a meses en los que el fuego natural es "
    "practicamente inexistente.",
    grafico_2,
)


# ==============================================================================
# CONSULTA 3 — CAUSA DOMINANTE POR ESTADO
# ==============================================================================
SQL_3 = """
WITH conteo AS (
    SELECT
        u.state_name        AS estado,
        c.descripcion_es    AS causa,
        o.descripcion       AS origen,
        COUNT(*)            AS eventos,
        SUM(COUNT(*)) OVER (PARTITION BY u.state_name) AS eventos_del_estado
    FROM incendios i
    JOIN causas    c ON i.cause_id    = c.cause_id
    JOIN origen    o ON c.origen_id   = o.origen_id
    JOIN ubicacion u ON i.location_id = u.location_id
    GROUP BY u.state_name, c.descripcion_es, o.descripcion
),
ranking AS (
    SELECT *, RANK() OVER (PARTITION BY estado ORDER BY eventos DESC) AS posicion
    FROM conteo
)
SELECT
    estado                                              AS "Estado",
    causa                                               AS "Causa dominante",
    origen                                              AS "Origen",
    eventos                                             AS "Eventos",
    ROUND(eventos * 100.0 / eventos_del_estado, 2)      AS "% del estado",
    eventos_del_estado                                  AS "Total del estado"
FROM ranking
WHERE posicion = 1
ORDER BY eventos_del_estado DESC
LIMIT 12;
"""

presentar(
    3,
    "Causa dominante en los estados de mayor carga",
    "Identifique, para cada estado, cual es la causa de incendio mas frecuente y "
    "que porcentaje representa sobre el total de incendios de ese estado. Muestre "
    "los doce estados con mayor numero de registros.",
    "`RANK()` particionado por estado para seleccionar el maximo de cada grupo, "
    "combinado con un total por particion calculado en la misma pasada.",
    SQL_3,
    "El patron de causas no es homogeneo en el territorio, y esa heterogeneidad "
    "tiene una logica geografica clara. En los estados del Sureste —Georgia, Texas, "
    "Carolina del Norte y Carolina del Sur— domina la **quema de desechos**, una "
    "practica agricola y domestica de temporada. En Misisipi y Alabama la causa "
    "dominante es el **incendio intencional**. En cambio, en Florida y Arizona la "
    "causa dominante es el **rayo**, unico origen natural del catalogo. California y "
    "Nueva York encabezan su ranking con la categoria residual *Miscelanea*, lo que "
    "no describe un fenomeno fisico sino una practica de registro: ambos estados "
    "clasifican una fraccion inusualmente alta de sus incendios en la categoria "
    "generica.",
)


# ==============================================================================
# CONSULTA 4 — EVOLUCION DE LA COMPOSICION POR ORIGEN
# ==============================================================================
SQL_4 = """
WITH anual AS (
    SELECT
        i.fire_year AS anio,
        COUNT(*)    AS total,
        SUM(CASE WHEN o.descripcion = 'Antropico'      THEN 1 ELSE 0 END) AS antropicos,
        SUM(CASE WHEN o.descripcion = 'Natural'        THEN 1 ELSE 0 END) AS naturales,
        SUM(CASE WHEN o.descripcion = 'No determinado' THEN 1 ELSE 0 END) AS indeterminados
    FROM incendios i
    JOIN causas c ON i.cause_id  = c.cause_id
    JOIN origen o ON c.origen_id = o.origen_id
    GROUP BY i.fire_year
)
SELECT
    anio                                                   AS "Anio",
    total                                                  AS "Total de incendios",
    ROUND(antropicos     * 100.0 / total, 2)               AS "% antropico",
    ROUND(naturales      * 100.0 / total, 2)               AS "% natural",
    ROUND(indeterminados * 100.0 / total, 2)               AS "% no determinado",
    ROUND(indeterminados * 100.0 / total
          - LAG(indeterminados * 100.0 / total) OVER (ORDER BY anio), 2)
                                                           AS "Variacion indeterminados (pp)"
FROM anual
ORDER BY anio;
"""


def grafico_4(df):
    largo = df.melt(
        id_vars="Anio",
        value_vars=["% antropico", "% natural", "% no determinado"],
        var_name="Origen", value_name="Porcentaje",
    )
    figura = px.line(
        largo, x="Anio", y="Porcentaje", color="Origen", markers=True,
        color_discrete_map={"% antropico": "#F25C05", "% natural": "#4FA3F7",
                            "% no determinado": "#8C8C8C"},
        title="Composicion anual por origen del fuego (%)",
    )
    figura.update_layout(template="plotly_dark", height=400)
    return figura


presentar(
    4,
    "Evolucion anual de la composicion por origen",
    "Calcule, para cada ano del periodo, la participacion porcentual de cada origen "
    "del fuego sobre el total de incendios registrados, e incluya la variacion "
    "interanual en puntos porcentuales de la categoria no determinada.",
    "Agregacion condicional con `CASE WHEN` dentro de `SUM` para construir varias "
    "series en una sola pasada, y `LAG` para la comparacion con el ano previo.",
    SQL_4,
    "La serie revela un fenomeno que conviene leer con cautela: la participacion de "
    "la categoria **no determinada crece de forma sostenida**, desde el 23,1% en 1992 "
    "hasta el 32,8% en 2015. Ese crecimiento no describe un cambio en el "
    "comportamiento del fuego, sino un cambio en la **practica de registro**: a "
    "medida que se incorporan mas agencias reportantes al sistema, aumenta la "
    "proporcion de incendios cuya causa no llega a establecerse. La consecuencia "
    "metodologica es directa: la caida aparente en la participacion del origen "
    "natural (de 18,0% a 13,2%) no debe interpretarse como una disminucion real de "
    "los incendios por rayo, sino en buena medida como un desplazamiento hacia la "
    "categoria residual. Es un ejemplo de por que un estudio descriptivo debe "
    "examinar la calidad del registro antes de atribuir significado a una tendencia.",
    grafico_4,
)


# ==============================================================================
# CONSULTA 5 — SEVERIDAD POR SECTOR DE PROPIEDAD
# ==============================================================================
SQL_5 = """
SELECT
    p.sector                                                       AS "Sector de propiedad",
    COUNT(*)                                                       AS "Eventos",
    ROUND(AVG(CASE WHEN o.descripcion = 'Antropico' THEN m.superficie_acres END), 2)
                                                                   AS "Media antropico (ac)",
    ROUND(AVG(CASE WHEN o.descripcion = 'Natural'   THEN m.superficie_acres END), 2)
                                                                   AS "Media natural (ac)",
    ROUND(
        AVG(CASE WHEN o.descripcion = 'Natural'   THEN m.superficie_acres END) /
        NULLIF(AVG(CASE WHEN o.descripcion = 'Antropico' THEN m.superficie_acres END), 0)
    , 1)                                                           AS "Razon natural / antropico"
FROM incendios  i
JOIN causas     c ON i.cause_id    = c.cause_id
JOIN origen     o ON c.origen_id   = o.origen_id
JOIN magnitud   m ON i.fire_id     = m.fire_id
JOIN propiedad  p ON i.owner_id    = p.owner_id
GROUP BY p.sector
HAVING COUNT(*) > 1000
ORDER BY "Eventos" DESC;
"""

presentar(
    5,
    "Severidad comparada por sector de propiedad del terreno",
    "Para cada sector de propiedad del terreno, calcule la superficie media quemada "
    "por los incendios de origen antropico y por los de origen natural, y obtenga la "
    "razon entre ambas. Considere unicamente los sectores con mas de mil eventos.",
    "Agregacion condicional (`AVG` sobre `CASE WHEN`) para calcular dos medias "
    "independientes en una sola agrupacion, con `NULLIF` como proteccion ante "
    "division por cero.",
    SQL_5,
    "En **todos** los sectores de propiedad sin excepcion, el incendio de origen "
    "natural quema en promedio mas superficie que el de origen humano. La razon, sin "
    "embargo, varia enormemente: en terrenos privados el fuego natural es unas 6 "
    "veces mayor, mientras que en tierras tribales la razon supera las 46 veces y en "
    "tierras estatales las 22 veces. La explicacion no es que el rayo sea mas "
    "'potente' en unas tierras que en otras, sino que se trata de un efecto de "
    "**ubicacion**: las tierras tribales, estatales y federales incluyen extensiones "
    "remotas, de baja densidad poblacional y acceso dificil, donde un incendio "
    "natural puede propagarse durante dias antes de ser alcanzado. Los terrenos "
    "privados y locales, mas proximos a la infraestructura, permiten una respuesta "
    "mucho mas temprana.",
)


# ==============================================================================
# CONSULTA 6 — CUARTILES DE SUPERFICIE POR ORIGEN
# ==============================================================================
SQL_6 = """
WITH cuartilizado AS (
    SELECT
        o.descripcion       AS origen,
        m.superficie_acres  AS acres,
        NTILE(4) OVER (PARTITION BY o.descripcion ORDER BY m.superficie_acres) AS cuartil
    FROM incendios i
    JOIN causas   c ON i.cause_id  = c.cause_id
    JOIN origen   o ON c.origen_id = o.origen_id
    JOIN magnitud m ON i.fire_id   = m.fire_id
)
SELECT
    origen                                    AS "Origen",
    cuartil                                   AS "Cuartil",
    COUNT(*)                                  AS "Eventos",
    ROUND(MIN(acres), 3)                      AS "Minimo (ac)",
    ROUND(MAX(acres), 1)                      AS "Maximo (ac)",
    ROUND(AVG(acres), 2)                      AS "Media (ac)",
    ROUND(SUM(acres), 0)                      AS "Acres del cuartil",
    ROUND(SUM(acres) * 100.0 / SUM(SUM(acres)) OVER (PARTITION BY origen), 2)
                                              AS "% de acres del origen"
FROM cuartilizado
GROUP BY origen, cuartil
ORDER BY origen, cuartil;
"""

presentar(
    6,
    "Cuartiles de superficie quemada dentro de cada origen",
    "Divida los incendios de cada origen en cuatro grupos de igual tamano segun su "
    "superficie quemada. Para cada cuartil informe su rango, su media y el "
    "porcentaje de la superficie total del origen que concentra.",
    "`NTILE(4)` particionado por origen para construir los cuartiles, y una funcion "
    "de ventana anidada sobre una agregacion (`SUM(SUM(...)) OVER`) para calcular la "
    "participacion relativa dentro de cada grupo.",
    SQL_6,
    "La cuartilizacion muestra que la concentracion extrema no es una peculiaridad "
    "del conjunto total, sino que **se reproduce dentro de cada origen por separado**. "
    "En los incendios naturales, el cuarto cuartil concentra el **99,93%** de la "
    "superficie del grupo; los tres primeros cuartiles juntos —el 75% de los eventos— "
    "aportan menos del 0,1%. En los antropicos la concentracion es algo menos "
    "extrema (97,46% en el cuarto cuartil), lo que indica una distribucion "
    "ligeramente menos desigual. Notese ademas la diferencia de escala: la media del "
    "cuarto cuartil natural (1.249,26 acres) es casi doce veces la del cuarto cuartil "
    "antropico (105,06 acres). Los tres primeros cuartiles de ambos origenes estan "
    "compuestos, en la practica, por conatos de menos de cuatro acres.",
)

st.caption(
    "Escuela de Estadistica y Ciencias Actuariales · Universidad Central de Venezuela · "
    "Material academico de la asignatura Computacion II."
)
