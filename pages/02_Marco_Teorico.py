"""
pages/02_Marco_Teorico.py
================================================================================
MARCO TEORICO DE LA INVESTIGACION
Origen del fuego: incendios antropicos vs. naturales, EE.UU. 1992-2015.
================================================================================

Reune los antecedentes empiricos, el contexto historico e institucional del
manejo del fuego en Estados Unidos, las bases conceptuales del fenomeno y los
fundamentos tecnicos de la arquitectura de datos empleada.
"""

import streamlit as st
import pandas as pd

st.set_page_config(page_title="Marco Teorico", page_icon="📚", layout="wide")

st.markdown("""
<style>
.justificado { text-align: justify; line-height: 1.65; }
.destacado   { color: #F25C05; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

st.title("Marco teorico")
st.caption("Fundamentos conceptuales, historicos y tecnicos de la investigacion")

# ==============================================================================
# 1. ANTECEDENTES
# ==============================================================================
st.header("1. Antecedentes de la investigacion")

st.subheader("1.1. La base FPA FOD como fuente cientifica")
st.markdown("""
<div class="justificado">
La <b>Fire Program Analysis fire-occurrence database</b> (FPA FOD) fue construida
originalmente para alimentar el sistema federal de analisis de programas de
fuego de Estados Unidos. Su cuarta edicion, compilada por
<b>Karen C. Short (2017)</b> y publicada por el Forest Service Research Data
Archive, integra los reportes de incendios de organismos federales, estatales y
locales bajo un unico estandar.<br><br>

La homologacion no fue trivial: cada sistema de reporte usaba sus propios
codigos, formatos de fecha y criterios de localizacion. Short aplico un proceso
de conformacion al estandar del <b>National Wildfire Coordinating Group (NWCG)</b>,
verificacion de errores y eliminacion de registros redundantes. Para que un
incendio fuese incluido debia contar con tres elementos minimos: fecha de
deteccion, superficie final y una localizacion con precision no menor a la
seccion del <i>Public Land Survey System</i>, es decir, una cuadricula de una
milla cuadrada.<br><br>

El producto resultante —1.880.465 registros que suman aproximadamente 140
millones de acres quemados en 24 anos— es hoy la fuente de referencia para el
estudio cuantitativo de la ocurrencia de incendios en ese pais.
</div>
""", unsafe_allow_html=True)

st.subheader("1.2. Antecedente directo: Balch y colaboradores (2017)")
st.markdown("""
<div class="justificado">
El antecedente mas cercano a esta investigacion es el trabajo de
<b>Balch, Bradley, Abatzoglou, Nagy, Fusco y Mahood (2017)</b>, publicado en
<i>Proceedings of the National Academy of Sciences</i> bajo el titulo
<i>"Human-started wildfires expand the fire niche across the United States"</i>.
Los autores analizaron esta misma base para el periodo 1992-2012 y establecieron
dos resultados que enmarcan el presente estudio:<br><br>

<b>Primero</b>, que la ignicion humana es responsable de la gran mayoria de los
incendios registrados. <b>Segundo</b>, y mas relevante conceptualmente, que la
actividad humana <span class="destacado">triplica la duracion de la temporada de
incendios</span>: al no depender de las tormentas electricas, el fuego de origen
humano se produce en meses en los que el fuego natural es practicamente
inexistente.<br><br>

Ese hallazgo es el que esta investigacion retoma y examina de manera descriptiva
sobre el periodo completo 1992-2015, incorporando ademas la dimension de
magnitud, que el trabajo citado aborda de forma secundaria.
</div>
""", unsafe_allow_html=True)

st.info("""
**Nota sobre la comparabilidad de las cifras.** La literatura suele reportar que
alrededor del **84%** de los incendios estadounidenses son de origen humano.
Esta investigacion reporta **59,11%**. La diferencia no es un error: responde a
dos criterios de clasificacion distintos.

Los trabajos que llegan al 84% asignan la causa *Miscellaneous* al bloque humano
y excluyen del denominador los registros *Missing/Undefined*. Aplicando ese mismo
criterio sobre nuestro modelo se obtiene **83,75%**, cifra plenamente consistente
con la literatura.

El presente estudio adopta un criterio mas conservador: mantiene *Miscelanea* y
*Ausente/No definida* como una tercera categoria de **causa no determinada**,
porque asignarlas al origen humano supone una imputacion que un diseno
descriptivo no deberia realizar. Ambas cifras son correctas bajo su respectivo
criterio; lo que no seria correcto es compararlas sin declarar el criterio.
""")

st.markdown("---")

# ==============================================================================
# 2. CONTEXTO HISTORICO E INSTITUCIONAL
# ==============================================================================
st.header("2. El manejo del fuego en Estados Unidos: contexto historico")

st.markdown("""
<div class="justificado">
Los datos analizados no son un registro neutral de un fenomeno natural: son el
producto de un sistema institucional con mas de un siglo de historia, cuyas
decisiones determinaron que se considera un incendio, quien lo reporta y con que
nivel de detalle. Comprender esa trayectoria es indispensable para interpretar
correctamente las cifras.
</div>
""", unsafe_allow_html=True)

hitos = pd.DataFrame({
    "Ano": ["1910", "1935", "1944", "1963", "1988", "1995", "2000", "2009"],
    "Hito": [
        "El Gran Incendio ('Big Blowup')",
        "Politica de las 10 de la manana",
        "Campana del oso Smokey",
        "Informe Leopold",
        "Incendios de Yellowstone",
        "Primera politica federal de manejo del fuego",
        "Plan Nacional de Incendios",
        "Ley FLAME",
    ],
    "Descripcion e implicacion para el registro del dato": [
        "Un complejo de incendios arraso cerca de tres millones de acres en Idaho y "
        "Montana. El episodio consolido al Servicio Forestal como la agencia federal "
        "responsable de la extincion y fundo una doctrina de supresion total.",

        "El Servicio Forestal establecio como meta contener todo incendio antes de "
        "las 10 de la manana del dia siguiente a su deteccion. Esta norma explica "
        "por que la variable de fecha de contencion se registra con tanto cuidado en "
        "los sistemas federales.",

        "El lanzamiento de la campana publica de prevencion introdujo la idea de que "
        "el incendio forestal es un problema de conducta humana, y con ello la "
        "necesidad de clasificar sistematicamente las causas.",

        "El informe sobre manejo de fauna en parques nacionales cuestiono la "
        "supresion total y reivindico el papel ecologico del fuego, abriendo paso a "
        "la distincion entre fuego natural y fuego no deseado.",

        "La quema de cerca de 1,2 millones de acres en el parque nacional puso a "
        "prueba la politica de dejar arder los fuegos naturales y forzo una revision "
        "nacional de los protocolos.",

        "La Politica Federal de Manejo del Fuego unifico criterios entre agencias y "
        "sento las bases del estandar NWCG que estructura los codigos empleados en "
        "esta base de datos.",

        "Tras una temporada especialmente severa, se destinaron recursos "
        "extraordinarios a la reduccion de combustible y se reforzaron los sistemas "
        "de informacion interagenciales.",

        "La ley de gestion de emergencias por incendios establecio fondos "
        "especificos y consolido la exigencia de reportes homogeneos, condicion que "
        "hizo posible una base como la FPA FOD.",
    ],
})
st.dataframe(hitos, width="stretch", hide_index=True)

st.markdown("---")

# ==============================================================================
# 3. BASES CONCEPTUALES
# ==============================================================================
st.header("3. Bases conceptuales")

col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("3.1. Regimen de fuego")
    st.markdown("""
    <div class="justificado">
    Se denomina <b>regimen de fuego</b> al patron caracteristico de frecuencia,
    intensidad, estacionalidad y extension que el fuego presenta en un ecosistema
    determinado a lo largo del tiempo. Cada ecosistema posee un regimen propio: las
    praderas templadas arden con alta frecuencia y baja intensidad, mientras que
    ciertos bosques de coniferas presentan incendios poco frecuentes pero de
    severidad extrema.<br><br>
    La introduccion de una fuente de ignicion humana permanente altera el regimen en
    su componente de <b>frecuencia</b> y, sobre todo, en su <b>estacionalidad</b>:
    el fuego deja de estar acotado a la ventana climatica que lo producia
    naturalmente.
    </div>
    """, unsafe_allow_html=True)

    st.subheader("3.2. Interfaz urbano-forestal")
    st.markdown("""
    <div class="justificado">
    La <b>interfaz urbano-forestal</b> (<i>wildland-urban interface</i>) es la zona
    de contacto entre las viviendas y la vegetacion silvestre. Es el area donde
    convergen las dos condiciones que producen el fuego antropico: presencia de
    fuentes de ignicion humanas y disponibilidad de combustible vegetal. Su
    expansion sostenida en Estados Unidos es la explicacion estructural de que las
    causas humanas dominen el conteo de eventos.
    </div>
    """, unsafe_allow_html=True)

with col_der:
    st.subheader("3.3. Causa estadistica NWCG")
    st.markdown("""
    <div class="justificado">
    El estandar del <b>National Wildfire Coordinating Group</b> define trece
    categorias de causa. La palabra <i>estadistica</i> en su denominacion es
    significativa: no se trata de una determinacion forense de la causa, sino de la
    categoria que la agencia reportante asigno con la informacion disponible al
    momento del reporte. De ahi que existan categorias residuales
    (<i>Miscellaneous</i>, <i>Missing/Undefined</i>) que agrupan casi el 26% de los
    registros y que esta investigacion trata como una categoria propia.
    </div>
    """, unsafe_allow_html=True)

    st.subheader("3.4. Clase de tamano y asimetria")
    st.markdown("""
    <div class="justificado">
    La escala de clases de tamano del NWCG (de A a G) es aproximadamente
    <b>logaritmica</b>: cada clase multiplica varias veces el techo de la anterior.
    Esa eleccion de escala no es arbitraria, sino un reconocimiento implicito de que
    la superficie quemada sigue una distribucion severamente asimetrica a la
    derecha, en la que unos pocos eventos concentran la mayor parte de la
    superficie. Es la misma razon por la que en este estudio la media aritmetica
    nunca se reporta sin su mediana.
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==============================================================================
# 4. FUNDAMENTOS DE LA ARQUITECTURA DE DATOS
# ==============================================================================
st.header("4. Fundamentos tecnicos de la arquitectura de datos")

st.subheader("4.1. Normalizacion y Tercera Forma Normal")
st.markdown("""
<div class="justificado">
La teoria de la normalizacion, formulada por <b>Edgar F. Codd</b>, establece una
serie de formas normales que eliminan progresivamente la redundancia y las
anomalias de actualizacion en una base relacional. Este proyecto normaliza hasta
la <span class="destacado">Tercera Forma Normal (3FN)</span>: toda tabla tiene
llave primaria, no contiene grupos repetitivos, todos sus atributos dependen de
la llave completa y ninguno depende de otro atributo no clave.<br><br>

El caso mas ilustrativo del proyecto es la relacion entre causa y origen. En la
fuente cruda, si se almacenara el origen junto a la causa en la tabla de hechos,
se produciria una <b>dependencia transitiva</b>: el origen no depende del
incendio, depende de la causa. La 3FN exige resolverla llevando esa relacion a la
dimension, que es exactamente lo que hace el modelo construido.
</div>
""", unsafe_allow_html=True)

st.subheader("4.2. Modelo dimensional en estrella")
st.markdown("""
<div class="justificado">
Frente al modelo puramente relacional, el <b>modelo dimensional</b> propuesto por
<b>Ralph Kimball</b> organiza el almacen analitico en torno a una o varias tablas
de <i>hechos</i> —que contienen las medidas— rodeadas de tablas de
<i>dimension</i> que contienen los atributos por los que se desea agrupar. El
diagrama resultante, con la tabla de hechos al centro, da nombre al esquema en
estrella.<br><br>

Su ventaja para el analisis descriptivo es directa: cualquier pregunta del tipo
"medida X agrupada por atributo Y" se resuelve con una sola union entre la tabla
de hechos y una dimension, sin recorrer cadenas largas de relaciones.
</div>
""", unsafe_allow_html=True)

st.subheader("4.3. Procesamiento analitico en linea (OLAP) y almacenamiento columnar")
st.markdown("""
<div class="justificado">
Los sistemas de bases de datos se disenan para uno de dos perfiles de carga.
El perfil <b>OLTP</b> (procesamiento transaccional en linea) atiende muchas
operaciones pequenas que leen y escriben filas completas. El perfil
<b>OLAP</b> (procesamiento analitico en linea) atiende pocas consultas que leen
pocas columnas de muchisimas filas y las agregan.<br><br>

Esta investigacion es enteramente OLAP: no inserta ni modifica registros, solo
agrega. De ahi la decision de trasladar el esquema normalizado a un formato de
<b>almacenamiento columnar</b> (Parquet), que guarda juntos los valores de una
misma columna. Ello habilita dos optimizaciones decisivas: la lectura selectiva
de columnas (<i>projection pushdown</i>) y una compresion muy superior, dado que
los valores contiguos son homogeneos. En este proyecto la reduccion alcanzada fue
de aproximadamente <b>6,5 veces</b> respecto de la base normalizada.<br><br>

Sobre esos archivos opera <b>DuckDB</b>, un motor analitico embebido de ejecucion
vectorizada que consulta los Parquet directamente, sin necesidad de cargarlos
integramente en memoria.
</div>
""", unsafe_allow_html=True)

st.markdown("---")
st.caption(
    "Escuela de Estadistica y Ciencias Actuariales · Universidad Central de Venezuela · "
    "Material academico de la asignatura Computacion II."
)
