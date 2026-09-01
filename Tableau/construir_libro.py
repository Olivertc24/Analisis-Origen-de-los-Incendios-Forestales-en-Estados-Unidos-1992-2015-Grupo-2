#!/usr/bin/env python3
"""
construir_libro.py
================================================================================
GENERACION DEL LIBRO DE TABLEAU (.twb) POR CODIGO
Investigacion: Origen del fuego (antropico vs. natural), EE.UU. 1992-2015.
Escuela de Estadistica y Ciencias Actuariales (EECA-UCV) — Computacion II
================================================================================

Un archivo .twb es XML: describe fuentes de datos, campos calculados, hojas y
tableros. Este script lo construye entero a partir de los extractos generados por
`generar_extractos.py`, de modo que el tablero es reproducible: si cambian los
datos, basta volver a ejecutar los dos scripts.

REGLAS DEL FORMATO QUE NO SON OBVIAS
------------------------------------
El validador de Tableau es estricto y su mensaje de error queda enmascarado en el
log (`error-details=["*****"]`); solo el dialogo de la aplicacion lo muestra
entero. Las reglas que hubo que respetar:

  * `<workbook>` necesita el atributo `source-build`.
  * `<document-format-change-manifest>` es obligatorio.
  * Cada `<worksheet>`, `<dashboard>` y `<window>` necesita su `<simple-id>`, y
    va SIEMPRE al final del elemento. Omitirlo produce:
        missing elements in content model '((layout-options?|repository-location?),table,simple-id)'
  * `<aggregation value='true' />` debe cerrar cada `<view>`.
  * El bloque `<windows>` es obligatorio y debe tener al menos una ventana no
    oculta. La ventana de un tablero exige `<viewpoints>` CON contenido (uno por
    hoja) y `<active>`.
  * Los elementos vacios se rechazan: nada de `<slices></slices>` ni `<style />`.
  * El orden dentro de `<view>` es estricto: filter, orden, slices, aggregation.
    Y el elemento de orden se llama `<computed-sort>`, no `<sort>`.
  * En una zona contenedora de tablero, `<zone-style>` va DESPUES de las zonas
    hijas.
  * La paleta de una dimension discreta se declara en el `<style>` de la FUENTE
    DE DATOS, no en el de la hoja, y sus `<bucket>` solo casan con cadenas
    entrecomilladas.
"""

import csv
import os
import re
import uuid
from xml.sax.saxutils import quoteattr, escape

DIRECTORIO = os.path.dirname(os.path.abspath(__file__))
EXTRACTOS = os.path.join(DIRECTORIO, "extractos")
SALIDA = os.path.join(DIRECTORIO, "Origen_del_Fuego_EEUU_1992_2015.twb")

SOURCE_BUILD = "0.0.0 (0000.25.1024.2150)"

MANIFEST = """  <document-format-change-manifest>
    <_.fcp.AccessibleZoneTabOrder.true...AccessibleZoneTabOrder />
    <_.fcp.AnimationOnByDefault.true...AnimationOnByDefault />
    <AutoCreateAndUpdateDSDPhoneLayouts />
    <_.fcp.MarkAnimation.true...MarkAnimation />
    <_.fcp.ObjectModelEncapsulateLegacy.true...ObjectModelEncapsulateLegacy />
    <_.fcp.ObjectModelTableType.true...ObjectModelTableType />
    <_.fcp.SchemaViewerObjectModel.true...SchemaViewerObjectModel />
    <SetMembershipControl />
    <SheetIdentifierTracking />
    <SortTagCleanup />
    <WindowsPersistSimpleIdentifiers />
  </document-format-change-manifest>"""

CARDS = """      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
          <strip size='2147483647'>
            <card type='rows' />
          </strip>
        </edge>
      </cards>"""

# ─────────────────────────────────────────────────────────── paleta Ember ──
# Los mismos colores del aplicativo de Streamlit: el color identifica el origen
# del fuego y no es decorativo.
NARANJA = "#F25C05"   # Antropico
AZUL    = "#4FA3F7"   # Natural
GRIS    = "#8C8C8C"   # No determinado
ROJO    = "#A62103"   # Superficie / alerta
DORADO  = "#F2A03D"   # Frecuencias
PAPEL     = "#F7F4F1"
SUPERFICIE = "#FFFFFF"
FILETE    = "#E0D8D2"
TINTA     = "#241C18"
TINTA_2   = "#4A3B33"
TINTA_3   = "#7A6A60"

COLOR_ORIGEN = {"Antropico": NARANJA, "Natural": AZUL, "No determinado": GRIS}

DS, CX = "federated.hechosincendios", "hyper.hechosincendios"
DSF, CXF = "federated.focosmuestra", "hyper.focosmuestra"

# Campos numericos que son codigos y no cantidades: deben ser dimension.
DIMENSIONES_NUMERICAS = {"Anio", "Mes", "Orden de clase", "Id foco"}

# Extraccion Hyper: Tableau Public solo publica libros basados en extracciones.
HYPER = "incendios_eeuu.hyper"

# Una tabla de la extraccion por cada extracto CSV.
TABLAS_HYPER = {
    "Hechos": "hechos_incendios.csv",
    "Focos": "focos_muestra.csv",
    "Resumen": "resumen_origen.csv",
}
TABLA_DE_CSV = {csv: tabla for tabla, csv in TABLAS_HYPER.items()}

# Codigos de tipo remoto del conector Hyper.
TIPO_REMOTO = {"integer": "20", "real": "5", "string": "130"}


def a(v):
    return quoteattr(str(v))


def sid(nombre):
    """<simple-id>, obligatorio en hojas, tableros y ventanas.

    Se deriva del nombre con UUID v5 para que regenerar el libro no cambie los
    identificadores y el control de versiones muestre solo cambios reales.
    """
    u = uuid.uuid5(uuid.NAMESPACE_URL, "eeca/incendios/" + nombre)
    return f"      <simple-id uuid='{{{str(u).upper()}}}' />"


# ──────────────────────────────────────────────────── esquema del extracto ──

def inferir(ruta, filas=400):
    """Deduce el tipo de cada columna del CSV a partir de una muestra."""
    with open(ruta, encoding="utf-8", newline="") as f:
        lector = csv.reader(f)
        cab = next(lector)
        m = {c: [] for c in cab}
        for i, fila in enumerate(lector):
            if i >= filas:
                break
            for c, v in zip(cab, fila):
                if v != "":
                    m[c].append(v)
    salida = []
    for orden, c in enumerate(cab):
        v = m[c]
        if v and all(re.fullmatch(r"-?\d+", x) for x in v):
            t = "integer"
        elif v and all(re.fullmatch(r"-?\d+(\.\d+)?([eE][-+]?\d+)?", x) for x in v):
            t = "real"
        else:
            t = "string"
        medida = t in ("integer", "real") and c not in DIMENSIONES_NUMERICAS
        salida.append({
            "n": c, "t": t, "orden": orden,
            "rol": "measure" if medida else "dimension",
            "clase": "quantitative" if medida else ("ordinal" if t != "string" else "nominal"),
        })
    return salida


# Sufijo del nombre interno segun el tipo del campo: nominal 'nk', ordinal 'ok',
# cuantitativo 'qk'. Equivocarlo hace que Tableau no resuelva la referencia.
SUFIJO = {"nominal": "nk", "ordinal": "ok", "quantitative": "qk"}


def instancia(col, derivacion, clase):
    """Nombre interno del uso concreto de un campo dentro de una hoja."""
    prefijo = "none" if derivacion == "None" else derivacion.lower()
    return f"[{prefijo}:{col}:{SUFIJO[clase]}]"


def ref(inst, ds=DS):
    return f"[{ds}].{inst}"


# ────────────────────────────────────────────────────── campos calculados ──
# Todos son cocientes de sumas y ninguno usa AVG(): promediar promedios produce
# una media no ponderada. Ver calculos/campos-calculados.md.
CALCULADOS = [
    ("AcresPromedio", "Acres promedio por incendio",
     "SUM([Acres]) / SUM([N incendios])", "n#,##0.00"),
    ("PctGrandes", "% de grandes incendios",
     "SUM([N grandes incendios]) / SUM([N incendios])", "p0.00%"),
    ("PctEventos", "% de eventos sobre el total",
     "SUM([N incendios]) / TOTAL(SUM([N incendios]))", "p0.00%"),
    ("PctAcres", "% de superficie sobre el total",
     "SUM([Acres]) / TOTAL(SUM([Acres]))", "p0.00%"),
    ("SeveridadRelativa", "Indice de severidad relativa",
     "(SUM([Acres]) / SUM([N incendios])) / TOTAL(SUM([Acres]) / SUM([N incendios]))",
     "n#,##0.00"),
]
INST_CALC = {k: f"[usr:{k}:qk]" for k, _, _, _ in CALCULADOS}


# Dimension calculada que duplica el origen del fuego. Existe por un motivo
# concreto: la paleta discreta declarada en el <style> de la fuente de datos solo
# se aplica sobre una dimension CALCULADA; sobre una columna nativa del archivo
# Tableau la ignora en silencio y pinta con su paleta por defecto.
DIM_ORIGEN = "OrigenFuego"
INST_ORIGEN = "[none:OrigenFuego:nk]"


def bloque_datasource(archivo, ds, cx, caption, calculados=(), paleta=None,
                      semantica=None, dims_calc=()):
    """Fuente de datos sobre una tabla de la extraccion Hyper.

    Tableau Public SOLO publica libros cuyas fuentes sean extracciones: una
    conexion en vivo a los CSV se abre en Tableau Desktop pero es rechazada al
    guardar en Tableau Public. Por eso la conexion es de clase `hyper` y apunta
    a `Data/<archivo>.hyper`, que es la ruta dentro del paquete .twbx.

    El esquema se sigue deduciendo del CSV de origen, de modo que el libro y la
    extraccion no puedan divergir: ambos salen del mismo archivo.
    """
    cols = inferir(os.path.join(EXTRACTOS, archivo))
    tabla = TABLA_DE_CSV[archivo]

    o = [f"  <datasource caption={a(caption)} inline='true' name='{ds}' version='18.1'>",
         "    <connection class='federated'>",
         "      <named-connections>",
         f"        <named-connection caption={a(caption)} name='{cx}'>",
         f"          <connection class='hyper' dbname='Data/{HYPER}' schema='Extract' "
         "server='' username='tableau_internal_user' />",
         "        </named-connection>",
         "      </named-connections>",
         f"      <relation connection='{cx}' name='{tabla}' "
         f"table='[Extract].[{tabla}]' type='table'>",
         "        <columns header='yes' outcome='6'>"]
    for c in cols:
        o.append(f"          <column datatype='{c['t']}' name={a(c['n'])} "
                 f"ordinal='{c['orden']}' />")
    o += ["        </columns>", "      </relation>", "      <metadata-records>"]
    for c in cols:
        o += ["        <metadata-record class='column'>",
              f"          <remote-name>{escape(c['n'])}</remote-name>",
              f"          <remote-type>{TIPO_REMOTO[c['t']]}</remote-type>",
              f"          <local-name>[{escape(c['n'])}]</local-name>",
              f"          <parent-name>[{tabla}]</parent-name>",
              f"          <remote-alias>{escape(c['n'])}</remote-alias>",
              f"          <ordinal>{c['orden']}</ordinal>",
              f"          <local-type>{c['t']}</local-type>",
              f"          <aggregation>{'Sum' if c['rol'] == 'measure' else 'Count'}</aggregation>",
              "          <contains-null>true</contains-null>",
              "        </metadata-record>"]
    o += ["      </metadata-records>", "    </connection>", "    <aliases enabled='yes' />"]

    semantica = semantica or {}
    for c in cols:
        # El rol geografico permite que Tableau dibuje un mapa real en lugar de
        # un diagrama de dispersion.
        rol_geo = (f" semantic-role={a(semantica[c['n']])}" if c["n"] in semantica else "")
        o.append(f"    <column datatype='{c['t']}' name={a('[' + c['n'] + ']')} "
                 f"role='{c['rol']}'{rol_geo} type='{c['clase']}' />")
    for clave, cap, formula, fmt in calculados:
        o += [f"    <column caption={a(cap)} datatype='real' default-format={a(fmt)} "
              f"name='[{clave}]' role='measure' type='quantitative'>",
              f"      <calculation class='tableau' formula={a(formula)} "
              "scope-isolation='false' />",
              "    </column>"]
    for clave, cap, formula in dims_calc:
        # El caption arregla de una vez el encabezado, el eje y el titulo del
        # filtro asociados al campo.
        o += [f"    <column caption={a(cap)} datatype='string' name='[{clave}]' "
              "role='dimension' type='nominal'>",
              f"      <calculation class='tableau' formula={a(formula)} "
              "scope-isolation='false' />",
              "    </column>",
              f"    <column-instance column='[{clave}]' derivation='None' "
              f"name={a('[none:' + clave + ':nk]')} pivot='key' type='nominal' />"]
    o.append("    <layout dim-ordering='alphabetic' measure-ordering='alphabetic' "
             "show-structure='true' />")
    if paleta:
        campo, mapa = paleta
        # La referencia va SIN el prefijo de la fuente de datos: con el, la
        # paleta se ignora en silencio y Tableau pinta con su paleta por defecto.
        inst = f"[none:{campo}:nk]"
        o += ["    <style>", "      <style-rule element='mark'>",
              f"        <encoding attr='color' field={a(inst)} type='palette'>"]
        for valor, color in mapa.items():
            # Tableau espera el hexadecimal en minusculas; en mayusculas ignora
            # la correspondencia sin avisar.
            o += [f"          <map to='{color.lower()}'>",
                  f"            <bucket>&quot;{escape(valor)}&quot;</bucket>",
                  "          </map>"]
        o += ["        </encoding>", "      </style-rule>", "    </style>"]
    o.append("  </datasource>")
    return o, {c["n"]: c for c in cols}


# ───────────────────────────────────────────────────────────────── hojas ──

def hoja(nombre, titulo, esquema, dims, medidas, calcs, filas, columnas, marca,
         ds=DS, caption="Hechos incendios", color=None, orden=None,
         filtros=(), estilo_extra=(), etiqueta=None, dims_calc=(), detalle=None):
    """Construye una hoja de trabajo completa."""
    o = [f"    <worksheet name={a(nombre)}>",
         "      <layout-options>", "        <title>", "          <formatted-text>",
         f"            <run fontcolor='{TINTA_2}' fontsize='11'>{escape(titulo)}</run>",
         "          </formatted-text>", "        </title>", "      </layout-options>",
         "      <table>", "        <view>", "          <datasources>",
         f"            <datasource caption={a(caption)} name='{ds}' />",
         "          </datasources>",
         f"          <datasource-dependencies datasource='{ds}'>"]

    usados = list(dict.fromkeys(list(dims) + list(filtros)))
    for d in usados:
        c = esquema[d]
        o.append(f"            <column datatype='{c['t']}' name={a('[' + d + ']')} "
                 f"role='dimension' type='{c['clase']}' />")
    for m in medidas:
        c = esquema[m]
        o.append(f"            <column datatype='{c['t']}' name={a('[' + m + ']')} "
                 f"role='measure' type='quantitative' />")
    for d in usados:
        c = esquema[d]
        o.append(f"            <column-instance column={a('[' + d + ']')} derivation='None' "
                 f"name={a(instancia(d, 'None', c['clase']))} pivot='key' "
                 f"type='{c['clase']}' />")
    for m in medidas:
        o.append(f"            <column-instance column={a('[' + m + ']')} derivation='Sum' "
                 f"name={a(instancia(m, 'Sum', 'quantitative'))} pivot='key' "
                 "type='quantitative' />")
    for clave, cap, formula in dims_calc:
        o += [f"            <column caption={a(cap)} datatype='string' name='[{clave}]' "
              "role='dimension' type='nominal'>",
              f"              <calculation class='tableau' formula={a(formula)} "
              "scope-isolation='false' />",
              "            </column>",
              f"            <column-instance column='[{clave}]' derivation='None' "
              f"name={a('[none:' + clave + ':nk]')} pivot='key' type='nominal' />"]
    for clave in calcs:
        cap, formula, fmt = next((c, f, x) for k, c, f, x in CALCULADOS if k == clave)
        o += [f"            <column caption={a(cap)} datatype='real' default-format={a(fmt)} "
              f"name='[{clave}]' role='measure' type='quantitative'>",
              f"              <calculation class='tableau' formula={a(formula)} "
              "scope-isolation='false' />",
              "            </column>",
              f"            <column-instance column='[{clave}]' derivation='User' "
              f"name={a(INST_CALC[clave])} pivot='key' type='quantitative' />"]
    o.append("          </datasource-dependencies>")

    # Orden dentro de <view>: filter, computed-sort, slices, aggregation.
    for i, f in enumerate(filtros):
        inst = instancia(f, "None", esquema[f]["clase"])
        o += [f"          <filter class='categorical' column={a(ref(inst, ds))} "
              f"filter-group='{100 + i}'>",
              f"            <groupfilter function='level-members' level={a(inst)} "
              "user:ui-enumeration='all' user:ui-marker='enumerate' />",
              "          </filter>"]
    if orden:
        campo_inst, medida_inst = orden
        o.append(f"          <computed-sort column={a(ref(campo_inst, ds))} "
                 f"direction='DESC' using={a(ref(medida_inst, ds))} />")
    if filtros:
        o.append("          <slices>")
        for f in filtros:
            o.append("            <column>"
                     + escape(ref(instancia(f, "None", esquema[f]["clase"]), ds))
                     + "</column>")
        o.append("          </slices>")
    o += ["          <aggregation value='true' />", "        </view>",
          "        <style>",
          "          <style-rule element='worksheet'>",
          "            <format attr='display-field-labels' scope='rows' value='false' />",
          "            <format attr='display-field-labels' scope='cols' value='false' />",
          "          </style-rule>",
          "          <style-rule element='pane'>",
          f"            <format attr='background-color' value='{SUPERFICIE}' />",
          "          </style-rule>",
          "          <style-rule element='axis'>",
          f"            <format attr='color' value='{TINTA_3}' />",
          "          </style-rule>",
          "          <style-rule element='header'>",
          f"            <format attr='color' value='{TINTA_2}' />",
          "          </style-rule>"]
    o += ["          " + l for l in estilo_extra]
    o += ["        </style>", "        <panes>",
          "          <pane selection-relaxation-option='selection-relaxation-allow'>",
          "            <view>", "              <breakdown value='auto' />",
          "            </view>",
          f"            <mark class='{marca}' />"]
    codificaciones = []
    if color:
        codificaciones.append(f"<color column={a(ref(color, ds))} />")
    if etiqueta:
        codificaciones.append(f"<text column={a(ref(etiqueta, ds))} />")
    if detalle:
        # <lod> fija el nivel de detalle de las marcas: una marca por valor del
        # campo. Es lo que convierte el mapa en 40.000 focos y no en un promedio.
        codificaciones.append(f"<lod column={a(ref(detalle, ds))} />")
    if codificaciones:
        o.append("            <encodings>")
        o += ["              " + c for c in codificaciones]
        o.append("            </encodings>")
    o += ["          </pane>", "        </panes>",
          f"        <rows>{escape(filas)}</rows>",
          f"        <cols>{escape(columnas)}</cols>",
          "      </table>", sid(nombre), "    </worksheet>"]
    return o


# ─────────────────────────────────────────────────── definicion del tablero ──

def i_dim(campo, esquema, ds=DS):
    return ref(instancia(campo, "None", esquema[campo]["clase"]), ds)


def i_med(campo, ds=DS):
    return ref(instancia(campo, "Sum", "quantitative"), ds)


def i_calc(clave, ds=DS):
    return ref(INST_CALC[clave], ds)


DIMS_ORIGEN = [(DIM_ORIGEN, "Origen del fuego", "[Origen del fuego]")]


def construir_hojas(esq, esqf):
    """Las doce hojas del tablero, en el orden en que se montan en las paginas."""
    inst_origen = INST_ORIGEN
    h = []

    # --- Pagina 1: panorama del origen ------------------------------------
    h += hoja("Eventos por origen", "Numero de incendios segun origen del fuego", esq,
              [], ["N incendios"], [], 
              i_med("N incendios"), ref(INST_ORIGEN), "Bar",
              color=inst_origen, dims_calc=DIMS_ORIGEN, filtros=["Anio", "Region censal"])
    h += hoja("Superficie por origen", "Superficie quemada segun origen del fuego", esq,
              [], ["Acres"], [], 
              i_med("Acres"), ref(INST_ORIGEN), "Bar",
              color=inst_origen, dims_calc=DIMS_ORIGEN, filtros=["Anio", "Region censal"])
    h += hoja("Estacionalidad por origen",
              "Distribucion mensual de incendios segun origen", esq,
              ["Mes"], ["N incendios"], [], 
              i_med("N incendios"), i_dim("Mes", esq), "Line",
              color=inst_origen, dims_calc=DIMS_ORIGEN, filtros=["Anio", "Region censal"])
    h += hoja("Severidad media por origen",
              "Acres promedio por incendio segun origen", esq,
              [], ["N incendios", "Acres"], ["AcresPromedio"], 
              i_calc("AcresPromedio"), ref(INST_ORIGEN), "Bar",
              color=inst_origen, dims_calc=DIMS_ORIGEN, filtros=["Anio", "Region censal"])

    # --- Pagina 2: magnitud, causas y propiedad ---------------------------
    h += hoja("Piramide de clases", "Incendios por clase de tamano NWCG", esq,
              ["Clase de tamano"], ["N incendios"], [],
              i_dim("Clase de tamano", esq), i_med("N incendios"), "Bar",
              color=instancia("Clase de tamano", "None", "nominal"),
              filtros=["Anio", "Region censal"])
    h += hoja("Superficie por clase", "Superficie quemada por clase de tamano", esq,
              ["Clase de tamano"], ["Acres"], [],
              i_dim("Clase de tamano", esq), i_med("Acres"), "Bar",
              color=instancia("Clase de tamano", "None", "nominal"),
              filtros=["Anio", "Region censal"])
    h += hoja("Causas del fuego", "Las trece causas estadisticas del NWCG", esq,
              ["Causa"], ["N incendios"], [], 
              i_dim("Causa", esq), i_med("N incendios"), "Bar",
              color=inst_origen, dims_calc=DIMS_ORIGEN,
              orden=(instancia("Causa", "None", "nominal"),
                     instancia("N incendios", "Sum", "quantitative")),
              filtros=["Anio", "Region censal"])
    h += hoja("Sector de propiedad", "Superficie quemada por tenencia de la tierra", esq,
              ["Sector de propiedad"], ["Acres"], [],
              i_dim("Sector de propiedad", esq), i_med("Acres"), "Bar",
              orden=(instancia("Sector de propiedad", "None", "nominal"),
                     instancia("Acres", "Sum", "quantitative")),
              filtros=["Anio", "Region censal"])

    # --- Pagina 3: geografia y evolucion ----------------------------------
    h += hoja("Ranking de estados", "Estados por superficie quemada", esq,
              ["Estado", "Region censal"], ["Acres"], [],
              i_dim("Estado", esq), i_med("Acres"), "Bar",
              color=instancia("Region censal", "None", "nominal"),
              orden=(instancia("Estado", "None", "nominal"),
                     instancia("Acres", "Sum", "quantitative")),
              filtros=["Anio"])
    h += hoja("Serie anual por origen", "Evolucion anual del numero de incendios", esq,
              ["Anio"], ["N incendios"], [], 
              i_med("N incendios"), i_dim("Anio", esq), "Line",
              color=inst_origen, dims_calc=DIMS_ORIGEN, filtros=["Region censal"])
    h += hoja("Region censal por origen", "Incendios por region censal y origen", esq,
              ["Region censal"], ["N incendios"], [], 
              i_med("N incendios"), i_dim("Region censal", esq), "Bar",
              color=inst_origen, dims_calc=DIMS_ORIGEN, filtros=["Anio"])
    # El mapa consume la muestra de focos individuales.
    h += hoja("Mapa de focos", "Muestra de 40.000 incendios geo-referenciados", esqf,
              ["Id foco"], [], [],
              ref(instancia("Latitud", "Avg", "quantitative"), DSF),
              ref(instancia("Longitud", "Avg", "quantitative"), DSF), "Circle",
              ds=DSF, caption="Focos muestra", color=INST_ORIGEN,
              dims_calc=DIMS_ORIGEN, filtros=["Anio"],
              detalle=instancia("Id foco", "None", "ordinal"))
    return h


# El mapa necesita declarar sus medidas con derivacion Avg, que la funcion
# generica declara como Sum. Se corrige el bloque de la hoja del mapa.
def parchar_mapa(lineas, esqf):
    salida = []
    for l in lineas:
        salida.append(l)
        if "<datasource-dependencies datasource='" + DSF + "'>" in l:
            for campo in ("Latitud", "Longitud"):
                salida.append(f"            <column datatype='real' name='[{campo}]' "
                              f"role='measure' semantic-role='[{'Latitude' if campo=='Latitud' else 'Longitude'}]' "
                              "type='quantitative' />")
                salida.append(f"            <column-instance column='[{campo}]' "
                              f"derivation='Avg' name='[avg:{campo}:qk]' pivot='key' "
                              "type='quantitative' />")
    return salida


# ─────────────────────────────────────────────────────────────── tableros ──

def zona_hoja(zid, nombre, x, y, w, h):
    return [f"        <zone h='{h}' id='{zid}' name={a(nombre)} w='{w}' x='{x}' y='{y}'>",
            "          <zone-style>",
            f"            <format attr='background-color' value='{SUPERFICIE}' />",
            f"            <format attr='border-color' value='{FILETE}' />",
            "            <format attr='border-style' value='solid' />",
            "            <format attr='border-width' value='1' />",
            "            <format attr='margin' value='5' />",
            "          </zone-style>", "        </zone>"]


def zona_texto(zid, texto, tam, color, negrita, x, y, w, h):
    """Zona de texto suelta. Titulo y subtitulo van en zonas distintas porque un
    salto de linea dentro de un mismo <formatted-text> no se respeta al
    renderizar el tablero."""
    return [f"        <zone h='{h}' id='{zid}' type-v2='text' w='{w}' x='{x}' y='{y}'>",
            "          <formatted-text>",
            f"            <run fontcolor='{color}' fontsize='{tam}'"
            f"{' bold=' + chr(39) + 'true' + chr(39) if negrita else ''}>"
            f"{escape(texto)}</run>",
            "          </formatted-text>",
            "          <zone-style>",
            f"            <format attr='background-color' value='{PAPEL}' />",
            "            <format attr='border-style' value='none' />",
            "            <format attr='border-width' value='0' />",
            "            <format attr='margin' value='4' />",
            "          </zone-style>", "        </zone>"]


def tablero(nombre, titulo, subtitulo, hojas_zonas):
    o = [f"    <dashboard name={a(nombre)}>",
         "      <style>",
         "        <style-rule element='dash-container'>",
         f"          <format attr='background-color' id='dash-zone_1' value='{PAPEL}' />",
         "        </style-rule>",
         "      </style>",
         "      <size maxheight='900' maxwidth='1500' minheight='900' minwidth='1500' />",
         "      <zones>",
         "        <zone h='100000' id='1' type-v2='layout-basic' w='100000' x='0' y='0'>"]
    o += zona_texto(2, titulo, 18, TINTA, True, 0, 0, 100000, 6500)
    o += zona_texto(3, subtitulo, 11, TINTA_3, False, 0, 6500, 100000, 4500)
    for i, (n, x, y, w, h) in enumerate(hojas_zonas, start=4):
        o += zona_hoja(i, n, x, y, w, h)
    # En una zona contenedora, <zone-style> va DESPUES de las zonas hijas.
    o += ["          <zone-style>",
          f"            <format attr='background-color' value='{PAPEL}' />",
          "            <format attr='border-style' value='none' />",
          "          </zone-style>",
          "        </zone>", "      </zones>", sid(nombre), "    </dashboard>"]
    return o


def ventanas(nombres_hojas, nombres_tableros):
    """Bloque <windows>: obligatorio, con al menos una ventana visible, y la de
    cada tablero con <viewpoints> con contenido y <active>."""
    o = ["  <windows source-height='30'>"]
    for i, nt in enumerate(nombres_tableros):
        o += [f"    <window class='dashboard' "
              f"{'maximized=' + chr(39) + 'true' + chr(39) + ' ' if i == 0 else ''}"
              f"name={a(nt)}>",
              "      <viewpoints>"]
        for n in nombres_hojas:
            o += [f"        <viewpoint name={a(n)}>",
                  "          <zoom type='entire-view' />",
                  "        </viewpoint>"]
        o += ["      </viewpoints>", "      <active id='-1' />",
              sid("win/" + nt), "    </window>"]
    for n in nombres_hojas:
        o += [f"    <window class='worksheet' hidden='true' name={a(n)}>",
              CARDS, sid("win/" + n), "    </window>"]
    o.append("  </windows>")
    return o


# ──────────────────────────────────────────────────────────────────── main ──

def main():
    ds_hechos, esq = bloque_datasource(
        "hechos_incendios.csv", DS, CX, "Hechos incendios",
        CALCULADOS, paleta=(DIM_ORIGEN, COLOR_ORIGEN), dims_calc=DIMS_ORIGEN)
    ds_focos, esqf = bloque_datasource(
        "focos_muestra.csv", DSF, CXF, "Focos muestra",
        paleta=(DIM_ORIGEN, COLOR_ORIGEN), dims_calc=DIMS_ORIGEN,
        semantica={"Latitud": "[Latitude]", "Longitud": "[Longitude]"})

    hojas_xml = parchar_mapa(construir_hojas(esq, esqf), esqf)
    nombres = [l.split("name=")[1].strip().strip(">").strip("'\"")
               for l in hojas_xml if l.startswith("    <worksheet ")]

    tableros = [
        tablero("1. Panorama del origen",
                "Origen del fuego en Estados Unidos, 1992-2015",
                "1.880.465 incendios geo-referenciados  ·  140,1 millones de acres quemados",
                [("Eventos por origen", 0, 11000, 50000, 44500),
                 ("Superficie por origen", 50000, 11000, 50000, 44500),
                 ("Estacionalidad por origen", 0, 55500, 50000, 44500),
                 ("Severidad media por origen", 50000, 55500, 50000, 44500)]),
        tablero("2. Magnitud, causas y propiedad",
                "La superficie se concentra en muy pocos incendios",
                "Clases de tamano NWCG, causas estadisticas y tenencia de la tierra",
                [("Piramide de clases", 0, 11000, 50000, 44500),
                 ("Superficie por clase", 50000, 11000, 50000, 44500),
                 ("Causas del fuego", 0, 55500, 50000, 44500),
                 ("Sector de propiedad", 50000, 55500, 50000, 44500)]),
        tablero("3. Geografia y evolucion",
                "Donde arde y como evoluciona",
                "Los estados con mas incendios no son los que mas superficie pierden",
                [("Mapa de focos", 0, 11000, 60000, 52000),
                 ("Ranking de estados", 60000, 11000, 40000, 89000),
                 ("Serie anual por origen", 0, 63000, 30000, 37000),
                 ("Region censal por origen", 30000, 63000, 30000, 37000)]),
    ]
    nombres_tableros = ["1. Panorama del origen", "2. Magnitud, causas y propiedad",
                        "3. Geografia y evolucion"]

    o = ["<?xml version='1.0' encoding='utf-8' ?>",
         f"<workbook source-build={a(SOURCE_BUILD)} source-platform='mac' version='18.1' "
         "xmlns:user='http://www.tableausoftware.com/xml/user'>",
         MANIFEST,
         "  <preferences>",
         "    <preference name='ui.encoding.shelf.height' value='24' />",
         "    <preference name='ui.shelf.height' value='26' />",
         "  </preferences>",
         "  <datasources>"]
    o += ds_hechos + ds_focos
    o += ["  </datasources>", "  <worksheets>"]
    o += hojas_xml
    o += ["  </worksheets>", "  <dashboards>"]
    for t in tableros:
        o += t
    o += ["  </dashboards>"]
    o += ventanas(nombres, nombres_tableros)
    o += ["</workbook>"]

    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write("\n".join(o))

    import xml.etree.ElementTree as ET
    ET.parse(SALIDA)   # falla si el XML no esta bien formado
    print(f"{os.path.basename(SALIDA)}: {len(o)} lineas, "
          f"{os.path.getsize(SALIDA)/1024:.0f} KB, XML bien formado")
    print(f"hojas: {len(nombres)} | tableros: {len(tableros)}")


if __name__ == "__main__":
    main()
