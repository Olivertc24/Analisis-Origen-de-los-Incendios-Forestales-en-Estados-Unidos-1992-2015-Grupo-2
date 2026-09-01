"""
03_procesamiento_carga.py
================================================================================
PROCESO ETL: EXTRACCION, TRANSFORMACION Y CARGA POR LOTES
Investigacion: Origen del fuego (antropico vs. natural), EE.UU. 1992-2015.
Escuela de Estadistica y Ciencias Actuariales (EECA-UCV) — Computacion II
================================================================================

PROPOSITO
---------
Migrar los 1.880.465 registros de la tabla unica `Fires` (base cruda de Kaggle)
al esquema normalizado creado por los scripts 01 y 02.

EL PROBLEMA DE MEMORIA
----------------------
La base cruda pesa 795 MB. Un `pd.read_sql_query()` sin control cargaria toda la
tabla en RAM de una sola vez, lo que en equipos de gama media provoca un
MemoryError o hace que el sistema operativo empiece a paginar a disco. La
solucion aplicada es la LECTURA POR LOTES (chunks) de 150.000 filas: en ningun
momento hay mas de un lote en memoria, por lo que el consumo se mantiene plano e
independiente del tamano total de la fuente.

TRANSFORMACIONES APLICADAS (y su justificacion)
-----------------------------------------------
 T1. Conversion de fechas julianas. La fuente almacena DISCOVERY_DATE como un
     numero real que representa el Dia Juliano (p. ej. 2453403.5). Se convierte
     a fecha ISO (YYYY-MM-DD) usando la funcion date() del propio SQLite, que
     interpreta nativamente ese formato. Hacerlo en el motor y no en pandas
     evita 1,88 millones de conversiones en Python.

 T2. Normalizacion de codigos a entero. STAT_CAUSE_CODE y OWNER_CODE vienen como
     float64 (1.0, 2.0, ...). Se convierten a entero para que coincidan con las
     llaves primarias de los catalogos.

 T3. Construccion incremental de la dimension `ubicacion`. La combinacion
     estado-condado se descubre recorriendo el dato. Se mantiene un diccionario
     en memoria (cache) para no consultar la base en cada fila: 1,88 millones de
     SELECT serian inviables, mientras que el cache resuelve la busqueda en
     tiempo constante.

 T4. Saneamiento de la dimension geografica. El campo COUNTY de la fuente es
     TEXTO LIBRE y no un catalogo: el mismo condado aparece escrito de hasta
     ocho formas distintas ('POTTAWATOMI', 'Pottawatomie', 'Potawatomi Co, KS',
     '149'...), y el 23,2% de los valores son en realidad codigos numericos y no
     nombres. Normalizar sobre ese campo produciria una dimension inflada, con
     el mismo condado repetido varias veces.

     La solucion aplicada es normalizar sobre el par (ESTADO, FIPS_CODE), que si
     es un identificador estable, y tratar el nombre del condado como una simple
     ETIQUETA de presentacion. Para elegir esa etiqueta se construye previamente
     un catalogo: por cada par estado-FIPS se toma la grafia alfabetica mas
     frecuente y se normaliza su capitalizacion. El resultado pasa de 6.070
     combinaciones espurias a 2.795 condados reales.

     Los registros sin FIPS (36,06% del total) NO se eliminan: el estado consta
     en el 100% de los casos y la unidad de analisis es el incendio, no el
     condado. Se agrupan en una entrada por estado con condado nulo, y la
     limitacion se documenta al descender a escala de condado.

 T5. Filtro de integridad de superficie. Se descartan los registros con
     FIRE_SIZE <= 0, fisicamente imposibles (un incendio registrado quemo
     alguna superficie). Se contabilizan y se reportan para dejar constancia
     del volumen depurado.

 T6. Campos derivados de magnitud. Se precalculan hectareas y la bandera de
     gran incendio (clases F y G), evitando recalcularlas en cada consulta.

ORDEN DE EJECUCION: tercero, despues de 01 y 02.
"""

import os
import sqlite3 as sql
import pandas as pd

# Se importa el diccionario de estados definido en el script de catalogos, para
# que exista una unica fuente de verdad de esa informacion en todo el proyecto.
from importlib import import_module
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
ESTADOS_EEUU = import_module('02_poblacion_catalogos').ESTADOS_EEUU


# ------------------------------------------------------------------------------
# CONFIGURACION
# ------------------------------------------------------------------------------

# Ruta a la base cruda descargada de Kaggle. Por su tamano (795 MB) este archivo
# NO se versiona en el repositorio; debe descargarse desde:
# https://www.kaggle.com/datasets/rtatman/188-million-us-wildfires
DB_ORIGEN = os.environ.get('FPA_FOD_PATH', '../../FPA_FOD_20170508.sqlite')

# Base normalizada producida por el script 01.
DB_DESTINO = 'incendios_eeuu_1992_2015.db'

# Tamano del lote. 150.000 filas es un equilibrio entre numero de transacciones
# (pocas, para no penalizar la escritura) y memoria ocupada (baja).
TAMANO_LOTE = 150_000

# Factor oficial de conversion de acres a hectareas.
ACRE_A_HECTAREA = 0.40468564224


# ------------------------------------------------------------------------------
# UTILIDADES
# ------------------------------------------------------------------------------

def construir_catalogo_condados(conn_origen):
    """
    Construye el catalogo canonico de condados (transformacion T4).

    Devuelve un diccionario {(estado, fips): nombre_canonico}.

    CRITERIO DE ELECCION DE LA ETIQUETA
    -----------------------------------
    Para cada par estado-FIPS se consideran todas las grafias observadas en la
    fuente y se aplica, en este orden:

        1. Se descartan las grafias puramente numericas, que son codigos y no
           nombres.
        2. Entre las restantes se elige la de mayor frecuencia de aparicion.
        3. Se normaliza la capitalizacion y los espacios sobrantes.

    Si un par no tiene ninguna grafia alfabetica, se devuelve None: es preferible
    un condado sin nombre a un condado etiquetado con un numero.
    """
    consulta = """
        SELECT STATE, FIPS_CODE, COUNTY, COUNT(*) AS apariciones
        FROM Fires
        WHERE FIPS_CODE IS NOT NULL AND COUNTY IS NOT NULL
        GROUP BY STATE, FIPS_CODE, COUNTY
    """

    candidatos = {}
    for estado, fips, condado, apariciones in conn_origen.execute(consulta):
        etiqueta = str(condado).strip()
        # Paso 1: descartar codigos numericos disfrazados de nombre.
        if not etiqueta or etiqueta.replace(' ', '').isdigit():
            continue
        clave = (estado, fips)
        # Paso 2: conservar la grafia mas frecuente.
        if clave not in candidatos or apariciones > candidatos[clave][1]:
            candidatos[clave] = (etiqueta, apariciones)

    # Paso 3: normalizar capitalizacion y espacios.
    catalogo = {}
    for clave, (etiqueta, _) in candidatos.items():
        limpio = ' '.join(etiqueta.split())          # colapsa espacios repetidos
        catalogo[clave] = limpio.title()             # 'POTTAWATOMIE' -> 'Pottawatomie'

    print(f"Catalogo de condados construido: {len(catalogo):,} condados canonicos.")
    return catalogo


def cargar_cache_ubicaciones(conn_destino):
    """
    Reconstruye en memoria el cache de la dimension `ubicacion`.

    Devuelve un diccionario {(state_code, fips_code): location_id}. La clave es
    el par estado-FIPS y no el nombre del condado, por las razones expuestas en
    la transformacion T4. Reconstruir el cache permite reanudar el ETL sin
    duplicar ubicaciones.
    """
    cache = {}
    for loc_id, estado, fips in conn_destino.execute(
            "SELECT location_id, state_code, fips_code FROM ubicacion"):
        cache[(estado, fips)] = loc_id
    return cache


def obtener_location_id(cache, conn_destino, catalogo_condados, estado, fips):
    """
    Devuelve el location_id de una combinacion estado-FIPS, creandola si es la
    primera vez que se observa (patron 'get or create').

    Es la implementacion practica de la transformacion T3: en lugar de repetir
    el texto del estado y el condado en cada una de los 1,88 millones de filas
    de hechos, se guarda una sola vez en la dimension y en los hechos queda un
    entero.

    El codigo FIPS identifica al condado dentro del estado y no depende del
    incendio, de modo que se registra al crear la combinacion y no se vuelve a
    tocar. Es una dependencia mas que la normalizacion saca de la tabla de
    hechos.
    """
    clave = (estado, fips)
    if clave in cache:
        return cache[clave]

    # El nombre del condado es una etiqueta de presentacion tomada del catalogo
    # canonico, no un dato de identificacion.
    condado = catalogo_condados.get(clave)

    # Se resuelven el nombre completo y la region censal desde el catalogo de
    # referencia. Si apareciera un codigo desconocido, se degrada con elegancia
    # en vez de interrumpir la carga completa.
    nombre_estado, region = ESTADOS_EEUU.get(estado, (estado, 'No clasificada'))

    cursor = conn_destino.execute(
        "INSERT INTO ubicacion (state_code, state_name, region_censo, county_name, fips_code) "
        "VALUES (?, ?, ?, ?, ?)",
        (estado, nombre_estado, region, condado, fips))
    cache[clave] = cursor.lastrowid
    return cache[clave]


def clase_a_id(letra):
    """Traduce la letra de clase NWCG (A-G) al class_id del catalogo (1-7)."""
    return {'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7}.get(letra)


# ------------------------------------------------------------------------------
# PROCESO PRINCIPAL
# ------------------------------------------------------------------------------

def procesar_y_cargar_por_lotes():
    """
    Ejecuta el ETL completo, lote por lote, desde la base cruda al esquema
    normalizado.
    """
    if not os.path.exists(DB_ORIGEN):
        raise FileNotFoundError(
            f"No se encontro la base cruda en '{DB_ORIGEN}'.\n"
            "Descarguela de Kaggle o indique la ruta con la variable de entorno "
            "FPA_FOD_PATH.")

    print("Iniciando extraccion y carga por lotes...")
    conn_origen = sql.connect(DB_ORIGEN)
    conn_destino = sql.connect(DB_DESTINO)
    conn_destino.execute("PRAGMA foreign_keys = ON;")

    # PRAGMAs de rendimiento: se sacrifica durabilidad ante un corte de energia
    # a cambio de velocidad de escritura. Es aceptable porque el proceso es
    # reproducible: si falla, se vuelve a correr desde cero.
    conn_destino.execute("PRAGMA journal_mode = WAL;")
    conn_destino.execute("PRAGMA synchronous = OFF;")

    # T4: catalogo canonico de condados, construido en una pasada previa.
    catalogo_condados = construir_catalogo_condados(conn_origen)
    cache_ubicaciones = cargar_cache_ubicaciones(conn_destino)

    # El fire_id es una llave subrogada correlativa propia del proyecto. Se
    # calcula el punto de partida para admitir cargas incrementales.
    ultimo = conn_destino.execute("SELECT MAX(fire_id) FROM registro_incendios").fetchone()[0]
    fire_id_global = (ultimo + 1) if ultimo is not None else 1
    print(f"Contador de fire_id inicializado en: {fire_id_global:,}")

    # --- T1: la conversion de fecha juliana se delega al motor de origen ------
    consulta = """
        SELECT
            FOD_ID,
            FIRE_YEAR,
            date(DISCOVERY_DATE)                              AS discovery_date,
            DISCOVERY_DOY,
            CAST(strftime('%m', date(DISCOVERY_DATE)) AS INT) AS discovery_month,
            DISCOVERY_TIME,
            STAT_CAUSE_CODE,
            OWNER_CODE,
            STATE,
            COUNTY,
            FIPS_CODE,
            LATITUDE,
            LONGITUDE,
            FIRE_SIZE,
            FIRE_SIZE_CLASS
        FROM Fires
    """

    lote_num = 0
    filas_leidas = 0
    filas_cargadas = 0
    descartadas_superficie = 0

    for lote in pd.read_sql_query(consulta, conn_origen, chunksize=TAMANO_LOTE):
        lote_num += 1
        filas_leidas += len(lote)

        # --- T5: filtro de integridad de superficie ---------------------------
        antes = len(lote)
        lote = lote[lote['FIRE_SIZE'] > 0].copy()
        descartadas_superficie += antes - len(lote)

        if lote.empty:
            continue

        # --- T2: codigos de catalogo a entero ---------------------------------
        lote['STAT_CAUSE_CODE'] = lote['STAT_CAUSE_CODE'].astype('int64')
        lote['OWNER_CODE'] = lote['OWNER_CODE'].astype('int64')

        # --- T3 y T4: resolucion de la dimension de ubicacion ------------------
        # Se normaliza el condado: cadenas vacias se tratan como ausencia real.
        lote['COUNTY'] = lote['COUNTY'].where(lote['COUNTY'].notna(), None)
        lote['FIPS_CODE'] = lote['FIPS_CODE'].where(lote['FIPS_CODE'].notna(), None)
        lote['location_id'] = [
            obtener_location_id(cache_ubicaciones, conn_destino, catalogo_condados,
                                estado, fips)
            for estado, fips in zip(lote['STATE'], lote['FIPS_CODE'])
        ]

        # --- Asignacion de la llave subrogada correlativa ----------------------
        n = len(lote)
        lote['fire_id'] = range(fire_id_global, fire_id_global + n)
        fire_id_global += n

        # --- Particionamiento hacia las dos tablas de hechos -------------------
        df_registro = lote[[
            'fire_id', 'FOD_ID', 'FIRE_YEAR', 'discovery_date', 'DISCOVERY_DOY',
            'discovery_month', 'DISCOVERY_TIME', 'STAT_CAUSE_CODE', 'location_id',
            'OWNER_CODE', 'LATITUDE', 'LONGITUDE'
        ]].rename(columns={
            'FOD_ID': 'fod_id',
            'FIRE_YEAR': 'fire_year',
            'DISCOVERY_DOY': 'discovery_doy',
            'DISCOVERY_TIME': 'discovery_time',
            'STAT_CAUSE_CODE': 'cause_id',
            'OWNER_CODE': 'owner_id',
            'LATITUDE': 'latitude',
            'LONGITUDE': 'longitude',
        })

        # --- T6: campos derivados de magnitud ---------------------------------
        df_magnitud = pd.DataFrame({
            'fire_id': lote['fire_id'],
            'class_id': lote['FIRE_SIZE_CLASS'].map(clase_a_id),
            'superficie_acres': lote['FIRE_SIZE'],
            'superficie_ha': (lote['FIRE_SIZE'] * ACRE_A_HECTAREA).round(4),
            'es_gran_incendio': lote['FIRE_SIZE_CLASS'].isin(['F', 'G']).astype('int8'),
        })

        # --- Carga -------------------------------------------------------------
        df_registro.to_sql('registro_incendios', conn_destino, if_exists='append', index=False)
        df_magnitud.to_sql('magnitud_incendio', conn_destino, if_exists='append', index=False)
        conn_destino.commit()

        filas_cargadas += n
        print(f"   Lote {lote_num:>3}: {filas_cargadas:>9,} registros acumulados "
              f"| ubicaciones distintas: {len(cache_ubicaciones):,}")

    conn_origen.close()
    conn_destino.close()

    print("-" * 70)
    print(f"Filas leidas de la fuente : {filas_leidas:,}")
    print(f"Descartadas (superficie<=0): {descartadas_superficie:,}")
    print(f"Filas cargadas            : {filas_cargadas:,}")
    print(f"Ubicaciones normalizadas  : {len(cache_ubicaciones):,}")


def verificar_integridad():
    """
    Control de calidad posterior a la carga.

    Verifica que no hayan quedado hechos huerfanos (referencias a catalogos
    inexistentes) y que la relacion 1:1 entre las dos tablas de hechos se
    cumpla. Un ETL sin verificacion no es un ETL: es una esperanza.
    """
    conn = sql.connect(DB_DESTINO)
    print("\nVERIFICACION DE INTEGRIDAD")
    print("-" * 70)

    controles = {
        "Registros en registro_incendios":
            "SELECT COUNT(*) FROM registro_incendios",
        "Registros en magnitud_incendio":
            "SELECT COUNT(*) FROM magnitud_incendio",
        "Hechos sin causa valida (debe ser 0)":
            "SELECT COUNT(*) FROM registro_incendios r "
            "LEFT JOIN causas c ON r.cause_id = c.cause_id WHERE c.cause_id IS NULL",
        "Hechos sin ubicacion valida (debe ser 0)":
            "SELECT COUNT(*) FROM registro_incendios r "
            "LEFT JOIN ubicacion u ON r.location_id = u.location_id WHERE u.location_id IS NULL",
        "Hechos sin propietario valido (debe ser 0)":
            "SELECT COUNT(*) FROM registro_incendios r "
            "LEFT JOIN propiedad_terreno p ON r.owner_id = p.owner_id WHERE p.owner_id IS NULL",
        "Magnitudes sin clase valida (debe ser 0)":
            "SELECT COUNT(*) FROM magnitud_incendio m "
            "LEFT JOIN clases_tamano t ON m.class_id = t.class_id WHERE t.class_id IS NULL",
        "Ruptura de la relacion 1:1 (debe ser 0)":
            "SELECT COUNT(*) FROM registro_incendios r "
            "LEFT JOIN magnitud_incendio m ON r.fire_id = m.fire_id WHERE m.fire_id IS NULL",
    }

    for etiqueta, consulta in controles.items():
        valor = conn.execute(consulta).fetchone()[0]
        print(f"   {etiqueta:<45} {valor:>12,}")

    conn.close()


# ==============================================================================
# BLOQUE DE EJECUCION
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("ETL — INCENDIOS FORESTALES EE.UU. 1992-2015")
    print("=" * 70)
    procesar_y_cargar_por_lotes()
    verificar_integridad()
