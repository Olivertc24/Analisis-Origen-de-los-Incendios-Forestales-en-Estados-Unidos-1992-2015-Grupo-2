"""
src/stats_logic.py
================================================================================
LOGICA ESTADISTICA DE LA INVESTIGACION
Origen del fuego: incendios antropicos vs. naturales, EE.UU. 1992-2015.
================================================================================

Este modulo concentra TODA la estadistica del proyecto. Las paginas del
aplicativo solo llaman funciones de aqui y dibujan el resultado; ninguna
calcula por su cuenta. Esa separacion (logica / presentacion) evita que la
misma medida se calcule de dos formas distintas en dos pantallas distintas.

CONTENIDO
---------
  1. Identidad visual (paleta y formato de cifras).
  2. Construccion del filtro maestro.
  3. Estadisticos descriptivos (tendencia central, dispersion, forma).
  4. Distribuciones de frecuencias.
  5. Analisis estacional, geografico y de magnitud.
  6. Generacion de lecturas automaticas.

NOTA METODOLOGICA
-----------------
La investigacion es de nivel DESCRIPTIVO. Todas las medidas se calculan sobre el
universo completo de registros (o sobre el subconjunto que el usuario filtre),
no sobre una muestra. Por lo tanto se emplean formulas poblacionales y no se
realizan pruebas de significacion ni estimaciones por intervalo.
"""

import streamlit as st
import pandas as pd


# ==============================================================================
# 1. IDENTIDAD VISUAL
# ==============================================================================

# Paleta "Ember": construida a partir de la fenomenologia del fuego forestal.
# El azul no es decorativo: identifica el origen natural (rayo), en oposicion
# cromatica al naranja del fuego de origen humano. La codificacion por color es
# consistente en toda la aplicacion y en el tablero de Tableau.
PALETA = {
    "ember_orange":   "#F25C05",   # Antropico
    "lightning_blue": "#4FA3F7",   # Natural
    "ash_gray":       "#8C8C8C",   # No determinado
    "coal_black":     "#0D0D0D",   # Fondo
    "smoke_white":    "#F2F2F2",   # Texto
    "burn_red":       "#A62103",   # Acentos de alerta / grandes incendios
    "dry_gold":       "#F2A03D",   # Acento secundario
}

# Asignacion fija de color por categoria de origen. Se exporta para que los
# graficos de Plotly usen exactamente los mismos colores que el resto de la
# interfaz.
COLOR_ORIGEN = {
    "Antropico":      PALETA["ember_orange"],
    "Natural":        PALETA["lightning_blue"],
    "No determinado": PALETA["ash_gray"],
}


def color_de_origen(origen):
    """Devuelve el color asociado a una categoria de origen."""
    return COLOR_ORIGEN.get(origen, PALETA["dry_gold"])


def formato_numero(valor, decimales=0, sufijo=""):
    """
    Formatea una cifra para tarjetas de indicadores.

    Aplica separador de miles y abrevia las magnitudes grandes (millones), que
    de otro modo resultan ilegibles en una tarjeta estrecha.
    """
    if valor is None or pd.isna(valor):
        return "s/d"
    valor = float(valor)
    if abs(valor) >= 1_000_000:
        return f"{valor/1_000_000:,.2f} M{sufijo}"
    if abs(valor) >= 1_000:
        return f"{valor:,.0f}{sufijo}"
    return f"{valor:,.{decimales}f}{sufijo}"


# ==============================================================================
# 2. FILTRO MAESTRO
# ==============================================================================

# Bloque FROM comun a casi todas las consultas. Se define una sola vez para que
# ninguna consulta pueda unir las tablas de forma distinta a las demas.
FROM_BASE = """
    FROM incendios i
    JOIN causas    c ON i.cause_id    = c.cause_id
    JOIN origen    o ON c.origen_id   = o.origen_id
    JOIN magnitud  m ON i.fire_id     = m.fire_id
    JOIN ubicacion u ON i.location_id = u.location_id
"""


def construir_filtro(origen="Todos", anio_inicio=1992, anio_fin=2015, region="Todas"):
    """
    Genera la clausula WHERE que comparten todas las consultas del aplicativo.

    Recibe el estado de los controles de la barra lateral y devuelve una cadena
    SQL. Centralizar esta construccion garantiza que los indicadores del
    encabezado y los graficos del cuerpo describan SIEMPRE el mismo subconjunto
    de datos: si cada consulta armara su propio filtro, bastaria una
    discrepancia para que la pantalla mostrara cifras incoherentes entre si.
    """
    condiciones = ["1 = 1"]

    if origen and origen != "Todos":
        # Se escapa la comilla simple por seguridad, aunque los valores provienen
        # de un control cerrado y no de texto libre del usuario.
        seguro = origen.replace("'", "''")
        condiciones.append(f"o.descripcion = '{seguro}'")

    condiciones.append(f"i.fire_year BETWEEN {int(anio_inicio)} AND {int(anio_fin)}")

    if region and region != "Todas":
        seguro = region.replace("'", "''")
        condiciones.append(f"u.region_censo = '{seguro}'")

    return " AND ".join(condiciones)


# ==============================================================================
# 3. INDICADORES Y ESTADISTICOS DESCRIPTIVOS
# ==============================================================================

@st.cache_data(show_spinner=False)
def obtener_indicadores(_qm, origen, anio_inicio, anio_fin, region):
    """
    Calcula los indicadores del encabezado del tablero.

    Devuelve una fila con: numero de eventos, superficie total quemada (acres y
    hectareas), superficie media por evento, superficie mediana y numero de
    grandes incendios (clases F y G).

    La MEDIANA se reporta junto a la MEDIA de forma deliberada. La distribucion
    de la superficie quemada es fuertemente asimetrica a la derecha: unos pocos
    incendios enormes arrastran la media muy por encima del valor tipico. Ver
    ambas cifras lado a lado hace visible esa asimetria, que es uno de los
    hallazgos de la investigacion.
    """
    filtro = construir_filtro(origen, anio_inicio, anio_fin, region)
    consulta = f"""
        SELECT
            COUNT(*)                                        AS eventos,
            SUM(m.superficie_acres)                         AS acres_totales,
            SUM(m.superficie_ha)                            AS hectareas_totales,
            AVG(m.superficie_acres)                         AS acres_promedio,
            MEDIAN(m.superficie_acres)                      AS acres_mediana,
            SUM(m.es_gran_incendio)                         AS grandes_incendios
        {FROM_BASE}
        WHERE {filtro}
    """
    return _qm.execute_query(consulta).iloc[0]


@st.cache_data(show_spinner=False)
def resumen_estadistico(_qm, origen, anio_inicio, anio_fin, region):
    """
    Construye el cuadro completo de estadisticos descriptivos de la superficie
    quemada, en acres.

    Incluye las tres familias que exige un analisis descriptivo:

      * TENDENCIA CENTRAL: media aritmetica y mediana.
      * POSICION: primer y tercer cuartil, y el percentil 90 y 99, necesarios
        para describir una cola derecha tan larga.
      * DISPERSION: rango, desviacion tipica, varianza y coeficiente de
        variacion. El CV se expresa en porcentaje y permite comparar la
        variabilidad entre grupos de magnitudes muy distintas, algo que la
        desviacion tipica por si sola no permite.
      * FORMA: coeficiente de asimetria. Un valor positivo alto confirma
        formalmente la cola derecha.
    """
    filtro = construir_filtro(origen, anio_inicio, anio_fin, region)
    consulta = f"""
        SELECT
            COUNT(*)                                   AS n,
            MIN(m.superficie_acres)                    AS minimo,
            MAX(m.superficie_acres)                    AS maximo,
            AVG(m.superficie_acres)                    AS media,
            MEDIAN(m.superficie_acres)                 AS mediana,
            QUANTILE_CONT(m.superficie_acres, 0.25)    AS q1,
            QUANTILE_CONT(m.superficie_acres, 0.75)    AS q3,
            QUANTILE_CONT(m.superficie_acres, 0.90)    AS p90,
            QUANTILE_CONT(m.superficie_acres, 0.99)    AS p99,
            STDDEV_POP(m.superficie_acres)             AS desviacion,
            VAR_POP(m.superficie_acres)                AS varianza,
            SKEWNESS(m.superficie_acres)               AS asimetria
        {FROM_BASE}
        WHERE {filtro}
    """
    fila = _qm.execute_query(consulta).iloc[0]

    # El rango intercuartilico y el coeficiente de variacion se derivan en
    # Python porque dependen de valores ya calculados; recalcularlos en SQL
    # obligaria a recorrer de nuevo el millon de filas.
    rango_intercuartilico = fila["q3"] - fila["q1"]
    coef_variacion = (fila["desviacion"] / fila["media"] * 100) if fila["media"] else None

    return {
        "n": fila["n"],
        "minimo": fila["minimo"],
        "maximo": fila["maximo"],
        "media": fila["media"],
        "mediana": fila["mediana"],
        "q1": fila["q1"],
        "q3": fila["q3"],
        "p90": fila["p90"],
        "p99": fila["p99"],
        "rango": fila["maximo"] - fila["minimo"],
        "rango_intercuartilico": rango_intercuartilico,
        "desviacion": fila["desviacion"],
        "varianza": fila["varianza"],
        "coef_variacion": coef_variacion,
        "asimetria": fila["asimetria"],
    }


@st.cache_data(show_spinner=False)
def comparativa_por_origen(_qm, anio_inicio, anio_fin, region):
    """
    Tabla comparativa de las tres categorias de origen.

    Es el nucleo de la investigacion: enfrenta la PARTICIPACION EN EVENTOS
    contra la PARTICIPACION EN SUPERFICIE. La divergencia entre ambas columnas
    es el hallazgo principal del estudio.
    """
    filtro = construir_filtro("Todos", anio_inicio, anio_fin, region)
    consulta = f"""
        WITH totales AS (
            SELECT COUNT(*) AS n_total, SUM(m.superficie_acres) AS acres_total
            {FROM_BASE}
            WHERE {filtro}
        )
        SELECT
            o.descripcion                                              AS "Origen",
            COUNT(*)                                                   AS "Eventos",
            ROUND(COUNT(*) * 100.0 / MAX(t.n_total), 2)                AS "% Eventos",
            ROUND(SUM(m.superficie_acres), 0)                          AS "Acres",
            ROUND(SUM(m.superficie_acres) * 100.0 / MAX(t.acres_total), 2) AS "% Acres",
            ROUND(AVG(m.superficie_acres), 2)                          AS "Acres promedio",
            ROUND(MEDIAN(m.superficie_acres), 2)                       AS "Acres mediana"
        {FROM_BASE}
        CROSS JOIN totales t
        WHERE {filtro}
        GROUP BY o.descripcion
        ORDER BY "Eventos" DESC
    """
    return _qm.execute_query(consulta)


# ==============================================================================
# 4. DISTRIBUCIONES DE FRECUENCIAS
# ==============================================================================

@st.cache_data(show_spinner=False)
def distribucion_causas(_qm, origen, anio_inicio, anio_fin, region):
    """
    Cuadro de distribucion de frecuencias de las 13 causas NWCG.

    Entrega las cuatro columnas de un cuadro de frecuencias clasico:
      fi  = frecuencia absoluta
      hi  = frecuencia relativa, en porcentaje
      Fi  = frecuencia absoluta acumulada
      Hi  = frecuencia relativa acumulada, en porcentaje

    Los encabezados se escriben con su nombre completo y no como 'fi'/'Fi' o
    'hi'/'Hi': los identificadores SQL no distinguen mayusculas de minusculas,
    de modo que esos pares colisionarian entre si y el motor renombraria las
    columnas por su cuenta (produciendo etiquetas como 'Fi_1').

    Las acumuladas se calculan con funciones de ventana (SUM ... OVER), lo que
    evita traer los datos a Python para acumularlos alli.
    """
    filtro = construir_filtro(origen, anio_inicio, anio_fin, region)
    consulta = f"""
        WITH conteo AS (
            SELECT
                c.descripcion_es        AS causa,
                o.descripcion           AS origen,
                COUNT(*)                AS frecuencia,
                SUM(m.superficie_acres) AS acres
            {FROM_BASE}
            WHERE {filtro}
            GROUP BY c.descripcion_es, o.descripcion
        ),
        total AS (SELECT SUM(frecuencia) AS n FROM conteo)
        SELECT
            causa                                            AS "Causa",
            origen                                           AS "Origen",
            frecuencia                                       AS "Frec. absoluta (fi)",
            ROUND(frecuencia * 100.0 / (SELECT n FROM total), 4)
                                                             AS "Frec. relativa (hi %)",
            SUM(frecuencia) OVER (ORDER BY frecuencia DESC)  AS "Frec. acumulada (Fi)",
            ROUND(SUM(frecuencia) OVER (ORDER BY frecuencia DESC) * 100.0
                  / (SELECT n FROM total), 4)                AS "Frec. rel. acumulada (Hi %)",
            ROUND(acres, 0)                                  AS "Acres quemados"
        FROM conteo
        ORDER BY frecuencia DESC
    """
    return _qm.execute_query(consulta)


@st.cache_data(show_spinner=False)
def distribucion_clases_tamano(_qm, origen, anio_inicio, anio_fin, region):
    """
    Distribucion por clase de tamano NWCG (A-G), con superficie asociada.

    Permite observar el contraste entre el numero de incendios de cada clase y
    la superficie que cada clase concentra: la piramide de frecuencias y la de
    superficie estan invertidas.
    """
    filtro = construir_filtro(origen, anio_inicio, anio_fin, region)
    consulta = f"""
        WITH conteo AS (
            SELECT cl.letra, cl.descripcion, cl.orden,
                   COUNT(*) AS fi, SUM(m.superficie_acres) AS acres
            {FROM_BASE}
            JOIN clases cl ON m.class_id = cl.class_id
            WHERE {filtro}
            GROUP BY cl.letra, cl.descripcion, cl.orden
        )
        SELECT
            letra                                                       AS "Clase",
            descripcion                                                 AS "Rango",
            fi                                                          AS "Eventos",
            ROUND(fi * 100.0 / SUM(fi) OVER (), 4)                      AS "% Eventos",
            ROUND(acres, 0)                                             AS "Acres",
            ROUND(acres * 100.0 / SUM(acres) OVER (), 4)                AS "% Acres"
        FROM conteo
        ORDER BY orden
    """
    return _qm.execute_query(consulta)


@st.cache_data(show_spinner=False)
def distribucion_propiedad(_qm, origen, anio_inicio, anio_fin, region):
    """
    Distribucion de eventos y superficie por sector de propiedad del terreno.

    Responde a la pregunta de sobre que tipo de tenencia de la tierra recae
    cada origen del fuego.
    """
    filtro = construir_filtro(origen, anio_inicio, anio_fin, region)
    consulta = f"""
        SELECT
            p.sector                                     AS "Sector",
            COUNT(*)                                     AS "Eventos",
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 3) AS "% Eventos",
            ROUND(SUM(m.superficie_acres), 0)            AS "Acres",
            ROUND(AVG(m.superficie_acres), 2)            AS "Acres promedio"
        {FROM_BASE}
        JOIN propiedad p ON i.owner_id = p.owner_id
        WHERE {filtro}
        GROUP BY p.sector
        ORDER BY "Eventos" DESC
    """
    return _qm.execute_query(consulta)


# ==============================================================================
# 5. ANALISIS ESTACIONAL, TEMPORAL Y GEOGRAFICO
# ==============================================================================

@st.cache_data(show_spinner=False)
def estacionalidad_mensual(_qm, anio_inicio, anio_fin, region):
    """
    Distribucion mensual de eventos, desglosada por origen.

    Es la evidencia central de la hipotesis estacional: el fuego antropico y el
    natural ocupan ventanas distintas del calendario. Se devuelve en formato
    largo (una fila por mes y origen) porque es el que consumen directamente
    los graficos de Plotly.
    """
    filtro = construir_filtro("Todos", anio_inicio, anio_fin, region)
    consulta = f"""
        SELECT
            cal.mes             AS "Mes",
            cal.abreviatura     AS "Mes abrev",
            cal.estacion        AS "Estacion",
            o.descripcion       AS "Origen",
            COUNT(*)            AS "Eventos",
            ROUND(SUM(m.superficie_acres), 0) AS "Acres"
        {FROM_BASE}
        JOIN calendario cal ON i.discovery_month = cal.mes
        WHERE {filtro}
        GROUP BY cal.mes, cal.abreviatura, cal.estacion, o.descripcion
        ORDER BY cal.mes, o.descripcion
    """
    return _qm.execute_query(consulta)


@st.cache_data(show_spinner=False)
def serie_anual(_qm, origen, anio_inicio, anio_fin, region):
    """
    Serie temporal anual de eventos y superficie quemada.

    Se incluye tambien la variacion interanual, calculada con la funcion de
    ventana LAG. Al tratarse de un estudio descriptivo, la serie se lee como
    descripcion del periodo observado y no como base de pronostico.
    """
    filtro = construir_filtro(origen, anio_inicio, anio_fin, region)
    consulta = f"""
        WITH base AS (
            SELECT i.fire_year AS anio,
                   COUNT(*) AS eventos,
                   SUM(m.superficie_acres) AS acres
            {FROM_BASE}
            WHERE {filtro}
            GROUP BY i.fire_year
        )
        SELECT
            anio                                          AS "Anio",
            eventos                                       AS "Eventos",
            ROUND(acres, 0)                               AS "Acres",
            ROUND(acres / NULLIF(eventos, 0), 2)          AS "Acres por evento",
            ROUND((eventos - LAG(eventos) OVER (ORDER BY anio)) * 100.0
                  / NULLIF(LAG(eventos) OVER (ORDER BY anio), 0), 2) AS "Variacion eventos (%)"
        FROM base
        ORDER BY anio
    """
    return _qm.execute_query(consulta)


@st.cache_data(show_spinner=False)
def ranking_estados(_qm, origen, anio_inicio, anio_fin, region, n=15, criterio="Eventos"):
    """
    Ranking de estados segun numero de eventos o superficie quemada.

    El parametro `criterio` permite alternar entre ambas ordenaciones, lo que
    hace visible que los estados que mas incendios registran no son
    necesariamente los que mas superficie pierden.
    """
    filtro = construir_filtro(origen, anio_inicio, anio_fin, region)
    columna_orden = '"Eventos"' if criterio == "Eventos" else '"Acres"'
    consulta = f"""
        SELECT
            u.state_name                              AS "Estado",
            u.state_code                              AS "Codigo",
            u.region_censo                            AS "Region",
            COUNT(*)                                  AS "Eventos",
            ROUND(SUM(m.superficie_acres), 0)         AS "Acres",
            ROUND(AVG(m.superficie_acres), 2)         AS "Acres promedio"
        {FROM_BASE}
        WHERE {filtro}
        GROUP BY u.state_name, u.state_code, u.region_censo
        ORDER BY {columna_orden} DESC
        LIMIT {int(n)}
    """
    return _qm.execute_query(consulta)


@st.cache_data(show_spinner=False)
def muestra_geografica(_qm, origen, anio_inicio, anio_fin, region, limite=25000):
    """
    Extrae una muestra de coordenadas para el mapa de dispersion.

    JUSTIFICACION DEL MUESTREO: dibujar 1,88 millones de puntos en el navegador
    lo bloquearia. Se toma una muestra aleatoria simple, que preserva la forma
    de la distribucion espacial.

    DETALLE TECNICO: se emplea `ORDER BY random() LIMIT n` y no la clausula
    `USING SAMPLE` de DuckDB. La razon es que el optimizador empuja el muestreo
    hasta la lectura del archivo, de modo que la muestra se toma ANTES de
    aplicar los filtros y el resultado final queda muy por debajo del tamano
    solicitado. El ordenamiento aleatorio con limite se resuelve mediante una
    seleccion de los n mejores y garantiza el tamano exacto de la muestra sobre
    el subconjunto ya filtrado.

    La muestra se usa UNICAMENTE para el mapa: todos los estadisticos del
    aplicativo se calculan sobre el universo completo.
    """
    filtro = construir_filtro(origen, anio_inicio, anio_fin, region)
    consulta = f"""
        SELECT
            i.latitude   AS lat,
            i.longitude  AS lon,
            o.descripcion AS origen,
            c.descripcion_es AS causa,
            m.superficie_acres AS acres,
            -- Peso visual en escala logaritmica. La superficie abarca ocho
            -- ordenes de magnitud (de 0,0001 a 606.945 acres): codificarla de
            -- forma lineal en el tamano del punto haria que el 99% de los
            -- incendios fuese invisible y solo se vieran tres o cuatro circulos.
            -- El logaritmo comprime la escala y hace legible la distribucion.
            LOG10(m.superficie_acres + 1) + 0.15 AS peso,
            i.fire_year AS anio
        {FROM_BASE}
        WHERE {filtro}
        ORDER BY random()
        LIMIT {int(limite)}
    """
    return _qm.execute_query(consulta)


# ==============================================================================
# 6. LECTURAS AUTOMATICAS
# ==============================================================================

def lectura_automatica(indicadores, origen):
    """
    Redacta una lectura breve de los indicadores segun el filtro activo.

    No es una interpretacion generada al azar: se apoya en la relacion entre la
    media y la mediana, que es la senal estadistica de la asimetria.
    """
    if indicadores["eventos"] == 0:
        return "No hay registros que cumplan los criterios seleccionados."

    media = indicadores["acres_promedio"]
    mediana = indicadores["acres_mediana"]
    razon = (media / mediana) if mediana else float("inf")

    encabezado = {
        "Antropico": "Perfil de origen humano",
        "Natural": "Perfil de origen natural",
        "No determinado": "Perfil de causa no establecida",
    }.get(origen, "Perfil del universo completo")

    return (
        f"**{encabezado}.** Se describen {formato_numero(indicadores['eventos'])} eventos "
        f"que suman {formato_numero(indicadores['acres_totales'])} acres. "
        f"La superficie media por incendio es de {media:,.2f} acres frente a una mediana "
        f"de {mediana:,.2f}: la media supera a la mediana en un factor de {razon:,.1f}, "
        f"lo que evidencia una distribucion fuertemente asimetrica a la derecha. "
        f"Los grandes incendios (clases F y G) suman "
        f"{formato_numero(indicadores['grandes_incendios'])} eventos."
    )


def ejecutar_consulta_libre(_qm, sentencia):
    """
    Ejecuta una consulta escrita por el usuario en la terminal SQL.

    Devuelve la tupla (DataFrame, error). Nunca lanza excepcion: la terminal
    debe informar el fallo sin tumbar la aplicacion.
    """
    resultado = _qm.execute_query(sentencia)
    if isinstance(resultado, str):
        return None, resultado
    return resultado, None
