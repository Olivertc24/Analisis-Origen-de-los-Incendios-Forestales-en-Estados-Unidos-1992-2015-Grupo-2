"""
app.py
================================================================================
TABLERO PRINCIPAL DEL APLICATIVO
Investigacion: Origen del fuego — incendios antropicos vs. naturales
Estados Unidos, 1992-2015. 1.880.465 registros geo-referenciados.
Escuela de Estadistica y Ciencias Actuariales (EECA-UCV) — Computacion II
================================================================================

Esta pagina es la vista de sintesis: presenta los indicadores generales del
universo filtrado y las cuatro evidencias centrales de la investigacion.

    1. La paradoja frecuencia-magnitud entre origen humano y natural.
    2. La estacionalidad diferenciada de ambos origenes.
    3. La concentracion de la superficie quemada en muy pocos eventos.
    4. La distribucion geografica del fenomeno.

Toda la estadistica proviene de `src/stats_logic.py`; aqui solo se dibuja.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from src.query_manager import get_query_manager
from src.stats_logic import (
    PALETA,
    COLOR_ORIGEN,
    formato_numero,
    obtener_indicadores,
    comparativa_por_origen,
    estacionalidad_mensual,
    distribucion_clases_tamano,
    ranking_estados,
    muestra_geografica,
    lectura_automatica,
)

# ==============================================================================
# CONFIGURACION DE LA PAGINA
# ==============================================================================
st.set_page_config(
    page_title="Origen del Fuego | EE.UU. 1992-2015",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ==============================================================================
# CONEXION AL DATA LAKE
# ==============================================================================
qm = get_query_manager()

if not qm.esta_completo():
    st.error(
        "No se encontro el Data Lake. Faltan los siguientes archivos en `data/`: "
        + ", ".join(qm.tablas_faltantes)
    )
    st.info(
        "Para generarlos, ejecute en orden los scripts de la carpeta "
        "`Base de datos/`:\n\n"
        "```\npython 01_creacion_esquema.py\n"
        "python 02_poblacion_catalogos.py\n"
        "python 03_procesamiento_carga.py\n"
        "python 04_exportacion_parquet.py\n```"
    )
    st.stop()


# ==============================================================================
# BARRA LATERAL — CONTROLES DEL UNIVERSO DE ANALISIS
# ==============================================================================
with st.sidebar:
    st.title("🔥 Panel de control")
    st.caption("Los controles delimitan el subconjunto sobre el que se calculan "
               "todos los estadisticos de esta pantalla.")

    origen_sel = st.radio(
        "Origen del fuego",
        ["Todos", "Antropico", "Natural", "No determinado"],
        help="Variable segmentadora de la investigacion. 'Todos' describe el universo completo.",
    )

    anio_ini, anio_fin = st.select_slider(
        "Periodo de observacion",
        options=list(range(1992, 2016)),
        value=(1992, 2015),
        help="La base cubre 24 anos completos, de 1992 a 2015.",
    )

    region_sel = st.selectbox(
        "Region censal",
        ["Todas", "Oeste", "Sur", "Medio Oeste", "Noreste"],
        help="Regiones de la Oficina del Censo de EE.UU.",
    )

    # El color de acento acompana la categoria seleccionada, de modo que la
    # interfaz refuerza visualmente que filtro esta activo.
    acento = COLOR_ORIGEN.get(origen_sel, PALETA["dry_gold"])
    st.markdown(
        f"<div style='border-left:6px solid {acento}; padding:10px 14px; "
        f"background:#161616; border-radius:4px; margin-top:10px;'>"
        f"<span style='color:{acento}; font-weight:700;'>Filtro activo</span><br>"
        f"<span style='color:#CCC; font-size:13px;'>{origen_sel} · {anio_ini}-{anio_fin} · {region_sel}</span>"
        f"</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.caption(
        "Fuente: Short, K. C. (2017). *Spatial wildfire occurrence data for the "
        "United States, 1992-2015* (FPA_FOD_20170508), 4a edicion. "
        "Forest Service Research Data Archive."
    )


# ==============================================================================
# ENCABEZADO E INDICADORES
# ==============================================================================
st.image("assets/banner_incendios.png", width="stretch")
st.markdown(
    "#### Perfil comparativo entre incendios de origen antropico y natural, 1992-2015"
)

indicadores = obtener_indicadores(qm, origen_sel, anio_ini, anio_fin, region_sel)

# Las unidades viajan en la etiqueta y no en el valor: una tarjeta de metrica
# es estrecha, y anteponer la unidad al numero provoca que el navegador lo
# recorte con puntos suspensivos.
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Incendios registrados", formato_numero(indicadores["eventos"]))
col2.metric("Superficie quemada (M acres)",
            f"{indicadores['acres_totales'] / 1_000_000:,.2f}")
col3.metric("Superficie media (acres)", f"{indicadores['acres_promedio']:,.2f}")
col4.metric("Superficie mediana (acres)", f"{indicadores['acres_mediana']:,.2f}")
col5.metric("Grandes incendios", formato_numero(indicadores["grandes_incendios"]),
            help="Clases F y G del estandar NWCG: 1.000 acres o mas.")

# Lectura automatica de los indicadores.
st.info(lectura_automatica(indicadores, origen_sel))

st.markdown("---")


# ==============================================================================
# EVIDENCIA 1 — LA PARADOJA FRECUENCIA / MAGNITUD
# ==============================================================================
st.header("1. Frecuencia frente a magnitud")
st.markdown(
    "El primer hallazgo de la investigacion surge de contrastar dos preguntas "
    "que suelen confundirse: **cuantos incendios** produce cada origen y "
    "**cuanta superficie** quema cada uno. Las respuestas no coinciden."
)

df_comparativa = comparativa_por_origen(qm, anio_ini, anio_fin, region_sel)

col_izq, col_der = st.columns([3, 2])

with col_izq:
    # Grafico de barras agrupadas: participacion en eventos vs. en superficie.
    figura = go.Figure()
    figura.add_trace(go.Bar(
        name="% de eventos",
        x=df_comparativa["Origen"],
        y=df_comparativa["% Eventos"],
        marker_color=PALETA["dry_gold"],
        text=df_comparativa["% Eventos"].map(lambda v: f"{v:.1f}%"),
        textposition="outside",
    ))
    figura.add_trace(go.Bar(
        name="% de superficie quemada",
        x=df_comparativa["Origen"],
        y=df_comparativa["% Acres"],
        marker_color=PALETA["burn_red"],
        text=df_comparativa["% Acres"].map(lambda v: f"{v:.1f}%"),
        textposition="outside",
    ))
    figura.update_layout(
        barmode="group",
        title="Participacion de cada origen en el total de eventos y de superficie",
        yaxis_title="Porcentaje del total (%)",
        xaxis_title="Origen del fuego",
        template="plotly_dark",
        height=430,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    st.plotly_chart(figura, width="stretch")

with col_der:
    st.subheader("Cuadro comparativo")
    st.dataframe(
        df_comparativa.style.format({
            "Eventos": "{:,.0f}",
            "% Eventos": "{:.2f}%",
            "Acres": "{:,.0f}",
            "% Acres": "{:.2f}%",
            "Acres promedio": "{:,.2f}",
            "Acres mediana": "{:,.2f}",
        }),
        width="stretch",
        hide_index=True,
    )
    st.caption(
        "La columna *Acres promedio* mide la severidad tipica de cada origen; "
        "la *mediana* muestra el incendio central de cada grupo. La distancia "
        "entre ambas es la firma de la asimetria."
    )

st.markdown("---")


# ==============================================================================
# EVIDENCIA 2 — ESTACIONALIDAD
# ==============================================================================
st.header("2. Estacionalidad diferenciada")
st.markdown(
    "Si el origen del fuego fuese indiferente al calendario, las tres curvas "
    "tendrian la misma forma. La distribucion mensual muestra lo contrario."
)

df_estacional = estacionalidad_mensual(qm, anio_ini, anio_fin, region_sel)

tab_eventos, tab_acres = st.tabs(["Por numero de eventos", "Por superficie quemada"])

with tab_eventos:
    figura_est = px.line(
        df_estacional,
        x="Mes abrev", y="Eventos", color="Origen",
        markers=True,
        color_discrete_map=COLOR_ORIGEN,
        title="Distribucion mensual de incendios segun origen",
        labels={"Mes abrev": "Mes", "Eventos": "Numero de incendios"},
    )
    figura_est.update_layout(template="plotly_dark", height=420,
                             margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(figura_est, width="stretch")
    st.caption(
        "El fuego antropico alcanza su maximo en primavera (marzo y abril), "
        "asociado a la quema de desechos agricolas. El fuego natural se "
        "concentra en pleno verano (julio y agosto), cuando la actividad "
        "convectiva produce tormentas electricas secas."
    )

with tab_acres:
    figura_acres = px.bar(
        df_estacional,
        x="Mes abrev", y="Acres", color="Origen",
        color_discrete_map=COLOR_ORIGEN,
        title="Superficie quemada por mes y origen",
        labels={"Mes abrev": "Mes", "Acres": "Superficie quemada (acres)"},
    )
    figura_acres.update_layout(template="plotly_dark", height=420, barmode="stack",
                               margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(figura_acres, width="stretch")
    st.caption(
        "Medida en superficie y no en numero de eventos, la estacionalidad se "
        "desplaza aun mas hacia el verano: los meses de fuego natural dominan "
        "el balance anual de hectareas perdidas."
    )

st.markdown("---")


# ==============================================================================
# EVIDENCIA 3 — CONCENTRACION DE LA SUPERFICIE
# ==============================================================================
st.header("3. Concentracion de la superficie en las clases mayores")
st.markdown(
    "Las clases de tamano del NWCG permiten ver hasta que punto el fenomeno "
    "esta dominado por sus valores extremos."
)

df_clases = distribucion_clases_tamano(qm, origen_sel, anio_ini, anio_fin, region_sel)

col_piramide, col_tabla = st.columns([3, 2])

with col_piramide:
    # Piramide opuesta: eventos hacia la izquierda, superficie hacia la derecha.
    figura_clases = go.Figure()
    figura_clases.add_trace(go.Bar(
        y=df_clases["Clase"], x=-df_clases["% Eventos"],
        name="% de eventos", orientation="h",
        marker_color=PALETA["dry_gold"],
        hovertemplate="Clase %{y}<br>%{customdata:.2f}% de los eventos<extra></extra>",
        customdata=df_clases["% Eventos"],
    ))
    figura_clases.add_trace(go.Bar(
        y=df_clases["Clase"], x=df_clases["% Acres"],
        name="% de superficie", orientation="h",
        marker_color=PALETA["burn_red"],
        hovertemplate="Clase %{y}<br>%{x:.2f}% de la superficie<extra></extra>",
    ))
    figura_clases.update_layout(
        barmode="relative",
        title="Piramide invertida: eventos frente a superficie por clase de tamano",
        xaxis_title="Porcentaje del total (%)   —   izquierda: eventos · derecha: superficie",
        yaxis_title="Clase NWCG",
        template="plotly_dark",
        height=430,
        margin=dict(l=20, r=20, t=60, b=20),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
    )
    st.plotly_chart(figura_clases, width="stretch")

with col_tabla:
    st.subheader("Distribucion por clase")
    st.dataframe(
        df_clases.style.format({
            "Eventos": "{:,.0f}", "% Eventos": "{:.3f}%",
            "Acres": "{:,.0f}", "% Acres": "{:.3f}%",
        }),
        width="stretch", hide_index=True,
    )
    st.caption(
        "Las dos piramides estan invertidas: las clases A y B reunen la enorme "
        "mayoria de los eventos y una fraccion marginal de la superficie, "
        "mientras que la clase G invierte por completo esa relacion."
    )

st.markdown("---")


# ==============================================================================
# EVIDENCIA 4 — GEOGRAFIA
# ==============================================================================
st.header("4. Distribucion geografica")

col_mapa, col_ranking = st.columns([3, 2])

with col_mapa:
    st.subheader("Localizacion de los focos")
    tamano_muestra = st.slider(
        "Tamano de la muestra a representar", 5_000, 50_000, 25_000, step=5_000,
        help="El mapa dibuja una muestra aleatoria. Los estadisticos de esta "
             "pagina se calculan siempre sobre el universo completo.",
    )
    df_mapa = muestra_geografica(qm, origen_sel, anio_ini, anio_fin, region_sel, tamano_muestra)

    figura_mapa = px.scatter_geo(
        df_mapa,
        lat="lat", lon="lon",
        color="origen",
        color_discrete_map=COLOR_ORIGEN,
        size="peso",          # Escala logaritmica: ver stats_logic.muestra_geografica
        size_max=16,
        opacity=0.5,
        scope="usa",
        hover_data={"causa": True, "anio": True, "acres": ":,.1f", "lat": False, "lon": False},
        title=f"Muestra aleatoria de {len(df_mapa):,} incendios",
    )
    figura_mapa.update_layout(template="plotly_dark", height=520,
                              margin=dict(l=0, r=0, t=60, b=0))
    figura_mapa.update_geos(bgcolor="rgba(0,0,0,0)", lakecolor="#101820",
                            landcolor="#1A1A1A", subunitcolor="#3A3A3A")
    st.plotly_chart(figura_mapa, width="stretch")

with col_ranking:
    st.subheader("Ranking de estados")
    criterio = st.radio(
        "Ordenar por", ["Eventos", "Acres"], horizontal=True,
        help="Los estados con mas incendios no son los que mas superficie pierden.",
    )
    df_ranking = ranking_estados(qm, origen_sel, anio_ini, anio_fin, region_sel, 12, criterio)

    figura_rank = px.bar(
        df_ranking.sort_values(criterio),
        x=criterio, y="Estado", orientation="h",
        color=criterio,
        color_continuous_scale=["#F2A03D", "#F25C05", "#A62103"],
        title=f"Doce primeros estados por {criterio.lower()}",
    )
    figura_rank.update_layout(template="plotly_dark", height=520,
                              coloraxis_showscale=False,
                              margin=dict(l=20, r=20, t=60, b=20))
    st.plotly_chart(figura_rank, width="stretch")

st.markdown("---")
st.caption(
    "Escuela de Estadistica y Ciencias Actuariales · Universidad Central de Venezuela · "
    "Material academico de la asignatura Computacion II."
)
