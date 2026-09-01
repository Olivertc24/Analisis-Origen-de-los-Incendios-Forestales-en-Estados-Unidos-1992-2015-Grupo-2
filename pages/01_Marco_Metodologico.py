"""
pages/01_Marco_Metodologico.py
================================================================================
MARCO METODOLOGICO DE LA INVESTIGACION
Origen del fuego: incendios antropicos vs. naturales, EE.UU. 1992-2015.
================================================================================

Esta pagina documenta el diseno de la investigacion: el problema, la pregunta
que la ordena, su nivel, la justificacion, los objetivos, la delimitacion del
universo y la operacionalizacion de las variables.

No realiza calculos: es la memoria metodologica del proyecto, publicada dentro
del propio aplicativo para que el lector pueda contrastar cada resultado con las
decisiones que lo hicieron posible.
"""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Marco Metodologico", page_icon="📐", layout="wide")

# --- Estilos reutilizados en toda la pagina -----------------------------------
st.markdown("""
<style>
.justificado { text-align: justify; line-height: 1.65; }
.destacado   { color: #F25C05; font-weight: 700; }
.tarjeta {
    background-color: #161616;
    border-left: 5px solid #F25C05;
    border-radius: 6px;
    padding: 16px 20px;
    margin-bottom: 12px;
    height: 100%;
}
.caja-pregunta {
    background-color: #101010;
    border-top: 4px solid #F25C05;
    border-bottom: 4px solid #F25C05;
    padding: 28px;
    border-radius: 8px;
    margin: 30px 0;
}
.etiqueta {
    color: #F25C05;
    font-size: 13px;
    text-transform: uppercase;
    letter-spacing: 2px;
    display: block;
    margin-bottom: 10px;
}
.texto-pregunta {
    color: #FFFFFF; font-size: 21px; font-style: italic;
    line-height: 1.55; text-align: center; margin: 0;
}
</style>
""", unsafe_allow_html=True)

st.image("assets/banner_incendios.png", width="stretch")
st.title("Marco metodologico")
st.caption("Origen del fuego en Estados Unidos · 1992-2015 · 1.880.465 registros")

# ==============================================================================
# 1. PLANTEAMIENTO DEL PROBLEMA
# ==============================================================================
st.header("1. Planteamiento del problema")

st.markdown("""
<div class="justificado">
El fuego es un componente natural de la mayoria de los ecosistemas forestales de
Estados Unidos. Durante milenios, las descargas electricas atmosfericas han
funcionado como agente de renovacion de bosques y praderas, y numerosas especies
vegetales dependen de esos ciclos para germinar. Sin embargo, la expansion de la
poblacion hacia la <span class="destacado">interfaz urbano-forestal</span> ha
introducido en ese sistema una fuente de ignicion nueva, permanente y de origen
humano.<br><br>

El resultado es un fenomeno de <b>doble naturaleza</b> que suele analizarse como
si fuera uno solo. Cuando se informa que un pais registro cierto numero de
incendios en un ano, esa cifra agrega dos procesos con logicas completamente
distintas: uno ligado a la actividad humana cotidiana y otro ligado a la
meteorologia. Confundirlos tiene consecuencias practicas, porque cada uno exige
una respuesta institucional diferente: el primero admite prevencion mediante
regulacion y educacion; el segundo solo admite deteccion temprana y capacidad
de respuesta.<br><br>

La base de datos <b>FPA FOD</b> (Fire Program Analysis fire-occurrence database),
publicada por el Servicio Forestal de Estados Unidos y compilada por Short (2017),
permite abordar empiricamente esa distincion. Reune 1.880.465 registros
geo-referenciados de incendios ocurridos entre 1992 y 2015, cada uno con su
fecha de deteccion, su superficie final, su localizacion y —de manera decisiva
para este estudio— su <b>causa estadistica</b> segun el estandar del National
Wildfire Coordinating Group.<br><br>

Ahora bien, el dato crudo no responde preguntas por si mismo. Se distribuye como
una unica tabla desnormalizada de 39 columnas y 795 megabytes, donde las
descripciones textuales se repiten cientos de miles de veces y donde no existe
ninguna variable que clasifique el origen del fuego. Para que ese conocimiento
sea, en terminos de <b>Arias (2012)</b>, <span class="destacado">metodicamente
obtenido y sistematicamente organizado</span>, se requiere un trabajo previo de
normalizacion, transformacion y construccion de variables que es parte
sustantiva de esta investigacion y no un mero paso tecnico.
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# PREGUNTA DE INVESTIGACION
# ==============================================================================
st.markdown("""
<div class="caja-pregunta">
    <span class="etiqueta">Interrogante de investigacion</span>
    <p class="texto-pregunta">
    "¿Como se diferencian los incendios forestales de origen antropico y los de
    origen natural registrados en Estados Unidos entre 1992 y 2015, en cuanto a
    su frecuencia, su magnitud, su distribucion estacional y su localizacion
    geografica?"
    </p>
</div>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. NIVEL DE INVESTIGACION
# ==============================================================================
st.header("2. Nivel de investigacion")

with st.expander("2.1. Nivel descriptivo", expanded=True):
    st.markdown("""
    <div class="justificado">
    De acuerdo con los objetivos formulados, esta investigacion se define como de
    <span class="destacado">nivel descriptivo</span>. Segun <b>Arias (2012)</b>, la
    investigacion descriptiva consiste en la caracterizacion de un hecho o fenomeno
    con el fin de establecer su estructura o comportamiento.<br><br>

    El estudio se limita, por tanto, a caracterizar el comportamiento de los
    incendios forestales registrados en el universo delimitado. No se formulan
    hipotesis a contrastar, no se realizan pruebas de significacion estadistica ni
    se estiman parametros poblacionales por intervalo. Las diferencias que se
    reportan entre categorias son <b>diferencias observadas en el universo
    completo</b>, no inferencias sobre una poblacion mayor.<br><br>

    Esta delimitacion es coherente con la naturaleza del dato: al trabajar con la
    totalidad de los registros disponibles y no con una muestra, las medidas
    calculadas son parametros del universo y no estimadores. En consecuencia, todas
    las formulas de dispersion empleadas son poblacionales.
    </div>
    """, unsafe_allow_html=True)

with st.expander("2.2. Diseno de la investigacion"):
    st.markdown("""
    <div class="justificado">
    El diseno es <b>no experimental</b> y de tipo <b>documental sobre fuente
    secundaria</b>. Los datos no fueron producidos por el equipo investigador: se
    trata de registros administrativos generados por agencias federales, estatales
    y locales de Estados Unidos en el ejercicio de sus funciones, posteriormente
    compilados, depurados y estandarizados por el Servicio Forestal.<br><br>

    Esta condicion impone dos consecuencias metodologicas que se asumen de forma
    explicita. Primero, las variables disponibles son las que el sistema de reporte
    decidio capturar, no las que idealmente exigiria el problema. Segundo, la
    calidad del registro varia entre agencias y a lo largo del tiempo, de modo que
    ciertos vacios de informacion —documentados en esta investigacion— son en si
    mismos un resultado y no un defecto a ocultar.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==============================================================================
# 3. JUSTIFICACION
# ==============================================================================
st.header("3. Justificacion de la investigacion")

st.markdown("""
<div class="justificado">
La relevancia del estudio se sostiene en tres planos. En el <b>plano sustantivo</b>,
separar el fuego antropico del natural permite dimensionar que porcion del
fenomeno es, al menos en principio, prevenible. En el <b>plano metodologico</b>,
el proyecto muestra que el analisis de un volumen de datos de esta escala es
viable con herramientas abiertas si se aplica una arquitectura adecuada. En el
<b>plano formativo</b>, articula en un solo producto los contenidos de diseno de
bases de datos, procesos ETL, estadistica descriptiva y visualizacion.
</div>
""", unsafe_allow_html=True)

st.subheader("Utilidad por area de aplicacion")

col_a, col_b = st.columns(2)
with col_a:
    st.markdown("""
    <div class="tarjeta"><b>🌲 Gestion forestal</b><br>
    Dimensionar que proporcion de la carga de incendios es atribuible a actividad
    humana y, por tanto, susceptible de politicas de prevencion.
    </div>""", unsafe_allow_html=True)
    st.markdown("""
    <div class="tarjeta"><b>📅 Planificacion operativa</b><br>
    Anticipar las ventanas del calendario en las que cada tipo de origen concentra
    su actividad, para distribuir recursos de vigilancia a lo largo del ano.
    </div>""", unsafe_allow_html=True)
with col_b:
    st.markdown("""
    <div class="tarjeta"><b>📊 Estadistica aplicada</b><br>
    Ilustrar el tratamiento de una distribucion severamente asimetrica, donde la
    media aritmetica es una medida enganosa si no se acompana de la mediana y de
    los cuantiles superiores.
    </div>""", unsafe_allow_html=True)
    st.markdown("""
    <div class="tarjeta"><b>💾 Arquitectura de datos</b><br>
    Demostrar la ganancia de normalizar una fuente desnormalizada y de sustituir un
    motor transaccional por uno columnar cuando la carga de trabajo es analitica.
    </div>""", unsafe_allow_html=True)

st.markdown("---")

# ==============================================================================
# 4. OBJETIVOS
# ==============================================================================
st.header("4. Definicion de objetivos")

st.markdown("""
<div style="background-color:#161616; border-top:4px solid #F25C05;
            border-bottom:4px solid #F25C05; padding:24px; border-radius:6px;
            margin-bottom:22px;">
    <p style="color:#F25C05; font-weight:700; text-transform:uppercase;
              letter-spacing:1px; font-size:13px; margin-bottom:8px;">Objetivo general</p>
    <p style="color:#FFF; font-size:18px; font-style:italic; line-height:1.55; margin:0;">
    Caracterizar de manera comparativa los incendios forestales de origen antropico
    y de origen natural registrados en Estados Unidos entre 1992 y 2015, a partir
    de su frecuencia, magnitud, estacionalidad y distribucion geografica, con el
    fin de construir perfiles diferenciados de ambos tipos de evento.
    </p>
</div>
""", unsafe_allow_html=True)

st.subheader("Objetivos especificos")
objetivos = [
    "Normalizar la base de datos original hasta la Tercera Forma Normal, "
    "construyendo un esquema en estrella que garantice la integridad referencial "
    "y elimine la redundancia de la fuente.",

    "Construir la variable *origen del fuego* a partir de la causa estadistica "
    "NWCG, mediante un criterio de clasificacion explicito y reproducible.",

    "Transformar el esquema normalizado en un Data Lake columnar en formato "
    "Parquet, de modo que el analisis de 1,88 millones de registros sea viable en "
    "un equipo de escritorio y en un despliegue web.",

    "Calcular los estadisticos descriptivos de tendencia central, posicion, "
    "dispersion y forma de la superficie quemada, para el universo completo y para "
    "cada categoria de origen.",

    "Describir la distribucion estacional de cada origen del fuego mediante "
    "distribuciones de frecuencias mensuales.",

    "Describir la distribucion geografica del fenomeno a escala de region censal, "
    "estado y condado.",

    "Desarrollar un aplicativo interactivo en Streamlit y un tablero en Tableau "
    "que permitan explorar la investigacion y reproducir sus resultados.",
]
for indice, objetivo in enumerate(objetivos, start=1):
    st.markdown(f"**{indice}.** {objetivo}")

st.markdown("---")

# ==============================================================================
# 5. UNIVERSO, UNIDAD DE ANALISIS Y TECNICAS
# ==============================================================================
st.header("5. Delimitacion del universo y tecnicas empleadas")

col_uni, col_unidad, col_tecnica = st.columns(3)
with col_uni:
    st.markdown("""
    <div class="tarjeta" style="border-left-color:#F25C05;">
    <h4 style="color:#F25C05; margin-top:0;">Universo</h4>
    <p style="font-size:14px;">La totalidad de los <b>1.880.465</b> incendios
    forestales geo-referenciados ocurridos en los 50 estados de Estados Unidos, el
    Distrito de Columbia y Puerto Rico entre el 1 de enero de 1992 y el 31 de
    diciembre de 2015, que cumplen los criterios de inclusion de la base FPA FOD:
    fecha de deteccion, superficie final y localizacion con precision minima de
    seccion PLSS.</p>
    </div>""", unsafe_allow_html=True)
with col_unidad:
    st.markdown("""
    <div class="tarjeta" style="border-left-color:#4FA3F7;">
    <h4 style="color:#4FA3F7; margin-top:0;">Unidad de analisis</h4>
    <p style="font-size:14px;">Cada <b>incendio individual</b> registrado,
    identificado en el modelo por la llave <code>fire_id</code> y trazable hasta la
    fuente original mediante <code>fod_id</code>. No se agregan eventos por
    complejo ni por incidente: cada reporte constituye una observacion.</p>
    </div>""", unsafe_allow_html=True)
with col_tecnica:
    st.markdown("""
    <div class="tarjeta" style="border-left-color:#F2A03D;">
    <h4 style="color:#F2A03D; margin-top:0;">Tecnicas</h4>
    <p style="font-size:14px;">Analisis documental de fuente secundaria y
    tratamiento estadistico descriptivo: distribuciones de frecuencias absolutas,
    relativas y acumuladas; medidas de tendencia central, de posicion, de
    dispersion y de forma.</p>
    </div>""", unsafe_allow_html=True)

st.markdown("")

st.subheader("Criterios de inclusion y exclusion aplicados")
st.markdown("""
| Criterio | Decision | Justificacion |
|---|---|---|
| Superficie final registrada | Se exige mayor que cero | Un incendio con superficie nula o negativa es fisicamente imposible; se trata de un error de captura. |
| Condado ausente (36,06% de los casos) | **Se conservan** los registros | El estado consta en el 100% de los casos y la unidad de analisis es el incendio, no el condado. La limitacion se declara al descender a escala de condado. |
| Grafias multiples del nombre de condado | Se normaliza sobre el par (estado, FIPS) | El campo `COUNTY` de la fuente es texto libre: un mismo condado aparece con hasta ocho escrituras distintas. Normalizar sobre el nombre habria inflado la dimension geografica y falseado toda frecuencia a escala de condado. |
| Hora de deteccion ausente (46,94%) | **Se conservan** los registros | El analisis se plantea a escala diaria y mensual; la hora no interviene en ninguna de las medidas reportadas. |
| Causa "Miscelanea" y "Ausente/No definida" | **Se conservan** como categoria propia | Repartirlas entre origen antropico y natural exigiria imputar, lo que introduciria un sesgo no justificable en un estudio descriptivo. |
""")

st.markdown("---")

# ==============================================================================
# 6. OPERACIONALIZACION DE VARIABLES
# ==============================================================================
st.header("6. Operacionalizacion de las variables")
st.markdown("""
<div class="justificado">
La siguiente tabla traduce los conceptos de la pregunta de investigacion en
variables medibles sobre el modelo de datos construido. La columna
<i>naturaleza</i> indica el tipo estadistico de cada variable, del que dependen
las medidas que es legitimo calcular sobre ella.
</div>
""", unsafe_allow_html=True)

variables = pd.DataFrame({
    "Dimension": [
        "Origen del fuego", "Origen del fuego",
        "Magnitud", "Magnitud", "Magnitud",
        "Temporalidad", "Temporalidad", "Temporalidad",
        "Geografia", "Geografia", "Contexto",
    ],
    "Variable / indicador": [
        "Origen del fuego", "Causa estadistica",
        "Superficie quemada", "Clase de tamano", "Gran incendio",
        "Ano de ocurrencia", "Mes de deteccion", "Dia juliano de deteccion",
        "Estado", "Region censal", "Propiedad del terreno",
    ],
    "Naturaleza": [
        "Cualitativa nominal", "Cualitativa nominal",
        "Cuantitativa continua", "Cualitativa ordinal", "Cualitativa dicotomica",
        "Cuantitativa discreta", "Cualitativa ordinal", "Cuantitativa discreta",
        "Cualitativa nominal", "Cualitativa nominal", "Cualitativa nominal",
    ],
    "Campo en el modelo": [
        "origen_fuego.descripcion", "causas.descripcion_es",
        "magnitud_incendio.superficie_acres", "clases_tamano.letra",
        "magnitud_incendio.es_gran_incendio",
        "registro_incendios.fire_year", "calendario_estacional.mes",
        "registro_incendios.discovery_doy",
        "ubicacion.state_name", "ubicacion.region_censo",
        "propiedad_terreno.sector",
    ],
    "Medidas aplicables": [
        "Frecuencias absolutas y relativas", "Frecuencias, cuadro de distribucion",
        "Media, mediana, cuartiles, desviacion, CV, asimetria",
        "Frecuencias y frecuencias acumuladas", "Proporcion",
        "Serie temporal, variacion interanual", "Distribucion estacional",
        "Distribucion anual acumulada",
        "Frecuencias, ranking", "Frecuencias, participacion relativa",
        "Frecuencias, superficie media por sector",
    ],
})
st.dataframe(variables, width="stretch", hide_index=True)

st.markdown("---")

# ==============================================================================
# 7. PROCESAMIENTO DE LA INFORMACION
# ==============================================================================
st.header("7. Procesamiento de la informacion")

st.markdown("""
El tratamiento del dato se organizo en cuatro fases encadenadas, cada una
implementada en un script reproducible de la carpeta `Base de datos/`:
""")

fases = pd.DataFrame({
    "Fase": ["1. Diseno del esquema", "2. Carga de catalogos",
             "3. Extraccion, transformacion y carga", "4. Data Lake analitico"],
    "Script": ["01_creacion_esquema.py", "02_poblacion_catalogos.py",
               "03_procesamiento_carga.py", "04_exportacion_parquet.py"],
    "Descripcion": [
        "Construccion de un esquema en estrella en Tercera Forma Normal: seis "
        "dimensiones y dos tablas de hechos en relacion 1:1, con llaves foraneas "
        "e indices de apoyo.",
        "Carga de los catalogos normativos del NWCG y construccion de la variable "
        "origen del fuego mediante un criterio de clasificacion explicito.",
        "Lectura por lotes de 150.000 filas, conversion de fechas julianas a "
        "formato ISO, normalizacion de la geografia y calculo de campos "
        "derivados, con verificacion posterior de integridad referencial.",
        "Exportacion del esquema a formato columnar Parquet con compresion ZSTD, "
        "sobre el que el aplicativo monta un motor DuckDB en memoria.",
    ],
})
st.dataframe(fases, width="stretch", hide_index=True)

st.success(
    "**Verificacion de la carga.** Al finalizar el proceso ETL se ejecutan siete "
    "controles de integridad: conteo de filas por tabla, ausencia de hechos "
    "huerfanos respecto de cada una de las cuatro dimensiones referenciadas, "
    "validez de la clase de tamano y cumplimiento de la relacion 1:1 entre las "
    "dos tablas de hechos. Los siete controles devuelven cero incidencias sobre "
    "los 1.880.465 registros cargados."
)

st.markdown("---")
st.caption(
    "Escuela de Estadistica y Ciencias Actuariales · Universidad Central de Venezuela · "
    "Material academico de la asignatura Computacion II."
)
