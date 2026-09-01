"""
02_poblacion_catalogos.py
================================================================================
POBLACION DE LAS TABLAS DE DIMENSION (CATALOGOS)
Investigacion: Origen del fuego (antropico vs. natural), EE.UU. 1992-2015.
Escuela de Estadistica y Ciencias Actuariales (EECA-UCV) — Computacion II
================================================================================

PROPOSITO
---------
Las dimensiones del modelo en estrella son catalogos pequenos y estables. No se
extraen de la base cruda por dos motivos metodologicos:

    1. TRAZABILIDAD: los codigos (STAT_CAUSE_CODE, OWNER_CODE, FIRE_SIZE_CLASS)
       provienen del estandar del National Wildfire Coordinating Group (NWCG) y
       de la documentacion de Short (2017). Escribirlos explicitamente deja
       constancia de la fuente normativa y no de lo que 'aparecio' en el dato.

    2. CONTROL DE CALIDAD: si en el ETL apareciera un codigo que no esta en el
       catalogo, la llave foranea lo rechazara. El catalogo actua entonces como
       una regla de validacion, no como un simple diccionario.

Las unicas dimensiones que NO se cargan aqui son:
    * `ubicacion`, que se puebla durante el ETL porque la combinacion
      estado-condado solo se conoce recorriendo el dato.

ORDEN DE EJECUCION: segundo, despues de 01_creacion_esquema.py.
"""

import sqlite3 as sql

DB_DESTINO = 'incendios_eeuu_1992_2015.db'


def abrir_conexion():
    """Conexion con integridad referencial activada (ver script 01)."""
    conn = sql.connect(DB_DESTINO)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ==============================================================================
# 1. ORIGEN DEL FUEGO — la variable segmentadora de la investigacion
# ==============================================================================

def poblar_origen_fuego():
    """
    Carga las tres categorias de origen que estructuran todo el estudio.

    CRITERIO DE CLASIFICACION (documentado y reproducible):
      - NATURAL: unicamente 'Lightning'. Es la unica causa del estandar NWCG
        que no requiere intervencion humana.
      - ANTROPICO: las diez causas que describen una actividad humana concreta
        (quema de desechos, incendio provocado, uso de equipos, fogatas,
        menores, fumadores, ferrocarril, lineas electricas, fuegos
        artificiales, estructuras).
      - NO DETERMINADO: 'Miscellaneous' y 'Missing/Undefined'. Se mantienen
        como categoria propia y NO se reparten entre las anteriores, porque
        imputarlas introduciria un sesgo no justificable en un estudio
        descriptivo.
    """
    datos = [
        (1, 'Antropico', 'Evitable',
         'Causas atribuibles a una actividad humana identificada en el reporte de incendio.'),
        (2, 'Natural', 'No evitable',
         'Ignicion por descarga electrica atmosferica (Lightning), sin intervencion humana.'),
        (3, 'No determinado', 'Indeterminada',
         'Causa no establecida o registrada como miscelanea por la agencia reportante.'),
    ]
    conn = abrir_conexion()
    conn.executemany(
        "INSERT OR REPLACE INTO origen_fuego (origen_id, descripcion, naturaleza, definicion) "
        "VALUES (?, ?, ?, ?)", datos)
    conn.commit()
    conn.close()
    print(f"[OK] origen_fuego: {len(datos)} categorias cargadas.")


# ==============================================================================
# 2. CAUSAS ESTADISTICAS NWCG (13 categorias)
# ==============================================================================

def poblar_causas():
    """
    Carga las 13 causas del campo STAT_CAUSE_CODE y las vincula a su origen.

    Los codigos y etiquetas en ingles son los del estandar NWCG tal como
    aparecen en la fuente; la traduccion al espanol se agrega como columna
    adicional para la interfaz del aplicativo, sin destruir la etiqueta
    original (principio de no perdida de informacion).
    """
    # (cause_id, etiqueta original, traduccion, origen_id)
    datos = [
        (1,  'Lightning',         'Rayo',                      2),
        (2,  'Equipment Use',     'Uso de equipos',            1),
        (3,  'Smoking',           'Fumadores',                 1),
        (4,  'Campfire',          'Fogata',                    1),
        (5,  'Debris Burning',    'Quema de desechos',         1),
        (6,  'Railroad',          'Ferrocarril',               1),
        (7,  'Arson',             'Incendio intencional',      1),
        (8,  'Children',          'Menores de edad',           1),
        (9,  'Miscellaneous',     'Miscelanea',                3),
        (10, 'Fireworks',         'Fuegos artificiales',       1),
        (11, 'Powerline',         'Linea electrica',           1),
        (12, 'Structure',         'Incendio estructural',      1),
        (13, 'Missing/Undefined', 'Ausente / No definida',     3),
    ]
    conn = abrir_conexion()
    conn.executemany(
        "INSERT OR REPLACE INTO causas (cause_id, descripcion_en, descripcion_es, origen_id) "
        "VALUES (?, ?, ?, ?)", datos)
    conn.commit()
    conn.close()
    print(f"[OK] causas: {len(datos)} causas NWCG cargadas.")


# ==============================================================================
# 3. CLASES DE TAMANO NWCG (A-G)
# ==============================================================================

def poblar_clases_tamano():
    """
    Carga la escala de clases de tamano del NWCG, medida en acres.

    La escala es logaritmica por diseno: cada clase multiplica varias veces el
    techo de la anterior. Esto refleja que la distribucion de la superficie
    quemada es fuertemente asimetrica a la derecha, hecho que la investigacion
    documenta empiricamente.
    """
    # (class_id, letra, limite_inf, limite_sup, descripcion, orden)
    datos = [
        (1, 'A', 0.0,     0.25,  'Mayor que 0 y hasta 0,25 acres',   1),
        (2, 'B', 0.26,    9.9,   'De 0,26 a 9,9 acres',              2),
        (3, 'C', 10.0,    99.9,  'De 10,0 a 99,9 acres',             3),
        (4, 'D', 100.0,   299.0, 'De 100 a 299 acres',               4),
        (5, 'E', 300.0,   999.0, 'De 300 a 999 acres',               5),
        (6, 'F', 1000.0,  4999.0,'De 1.000 a 4.999 acres',           6),
        (7, 'G', 5000.0,  None,  'De 5.000 acres en adelante',       7),
    ]
    conn = abrir_conexion()
    conn.executemany(
        "INSERT OR REPLACE INTO clases_tamano "
        "(class_id, letra, limite_inf, limite_sup, descripcion, orden) VALUES (?, ?, ?, ?, ?, ?)",
        datos)
    conn.commit()
    conn.close()
    print(f"[OK] clases_tamano: {len(datos)} clases NWCG cargadas.")


# ==============================================================================
# 4. PROPIEDAD DEL TERRENO (16 categorias + jerarquia de sector)
# ==============================================================================

def poblar_propiedad_terreno():
    """
    Carga el catalogo de propietarios del terreno en el punto de origen.

    La columna 'sector' es una agregacion propia de la investigacion: reduce 16
    categorias operativas a 6 macrocategorias comparables. Esto permite
    responder preguntas del tipo "que proporcion del fuego antropico ocurre en
    tierras federales" sin escribir listas de codigos en cada consulta.
    """
    # (owner_id, descripcion original, sector agregado)
    datos = [
        (0,  'FOREIGN',               'Extranjero'),
        (1,  'BLM',                   'Federal'),
        (2,  'BIA',                   'Federal'),
        (3,  'NPS',                   'Federal'),
        (4,  'FWS',                   'Federal'),
        (5,  'USFS',                  'Federal'),
        (6,  'OTHER FEDERAL',         'Federal'),
        (7,  'STATE',                 'Estatal'),
        (8,  'PRIVATE',               'Privado'),
        (9,  'TRIBAL',                'Tribal'),
        (10, 'BOR',                   'Federal'),
        (11, 'COUNTY',                'Local'),
        (12, 'MUNICIPAL/LOCAL',       'Local'),
        (13, 'STATE OR PRIVATE',      'Mixto estatal-privado'),
        (14, 'MISSING/NOT SPECIFIED', 'No especificado'),
        (15, 'UNDEFINED FEDERAL',     'Federal'),
    ]
    conn = abrir_conexion()
    conn.executemany(
        "INSERT OR REPLACE INTO propiedad_terreno (owner_id, descripcion, sector) "
        "VALUES (?, ?, ?)", datos)
    conn.commit()
    conn.close()
    print(f"[OK] propiedad_terreno: {len(datos)} propietarios cargados.")


# ==============================================================================
# 5. CALENDARIO ESTACIONAL (12 meses)
# ==============================================================================

def poblar_calendario_estacional():
    """
    Carga la dimension de calendario con atributos estacionales.

    'temporada_fuego' es una clasificacion operativa construida a partir del
    propio comportamiento observado en la base (volumen mensual de eventos):
        - Alta:  marzo, abril, julio y agosto (los cuatro meses de mayor carga)
        - Media: febrero, mayo, junio, septiembre, octubre
        - Baja:  enero, noviembre, diciembre
    Se declara explicitamente por transparencia metodologica: es una categoria
    construida por el equipo, no un campo de la fuente.
    """
    datos = [
        (1,  'Enero',      'Ene', 'Invierno',  'Baja'),
        (2,  'Febrero',    'Feb', 'Invierno',  'Media'),
        (3,  'Marzo',      'Mar', 'Primavera', 'Alta'),
        (4,  'Abril',      'Abr', 'Primavera', 'Alta'),
        (5,  'Mayo',       'May', 'Primavera', 'Media'),
        (6,  'Junio',      'Jun', 'Verano',    'Media'),
        (7,  'Julio',      'Jul', 'Verano',    'Alta'),
        (8,  'Agosto',     'Ago', 'Verano',    'Alta'),
        (9,  'Septiembre', 'Sep', 'Otono',     'Media'),
        (10, 'Octubre',    'Oct', 'Otono',     'Media'),
        (11, 'Noviembre',  'Nov', 'Otono',     'Baja'),
        (12, 'Diciembre',  'Dic', 'Invierno',  'Baja'),
    ]
    conn = abrir_conexion()
    conn.executemany(
        "INSERT OR REPLACE INTO calendario_estacional "
        "(mes, nombre_mes, abreviatura, estacion, temporada_fuego) VALUES (?, ?, ?, ?, ?)", datos)
    conn.commit()
    conn.close()
    print(f"[OK] calendario_estacional: {len(datos)} meses cargados.")


# ==============================================================================
# 6. TABLA DE REFERENCIA DE ESTADOS (consumida por el ETL)
# ==============================================================================

# Diccionario auxiliar: codigo de dos letras -> (nombre, region del Censo).
# No es una tabla de la base; es un recurso que el script 03 importa para
# construir la dimension `ubicacion` sobre la marcha. Se mantiene aqui para
# que toda la informacion de catalogo viva en un unico archivo.
# Las cuatro regiones son las de la Oficina del Censo de EE.UU. Puerto Rico y
# el Distrito de Columbia se asignan segun su tratamiento censal habitual.
ESTADOS_EEUU = {
    'AL': ('Alabama',              'Sur'),
    'AK': ('Alaska',               'Oeste'),
    'AZ': ('Arizona',              'Oeste'),
    'AR': ('Arkansas',             'Sur'),
    'CA': ('California',           'Oeste'),
    'CO': ('Colorado',             'Oeste'),
    'CT': ('Connecticut',          'Noreste'),
    'DE': ('Delaware',             'Sur'),
    'DC': ('Distrito de Columbia', 'Sur'),
    'FL': ('Florida',              'Sur'),
    'GA': ('Georgia',              'Sur'),
    'HI': ('Hawai',                'Oeste'),
    'ID': ('Idaho',                'Oeste'),
    'IL': ('Illinois',             'Medio Oeste'),
    'IN': ('Indiana',              'Medio Oeste'),
    'IA': ('Iowa',                 'Medio Oeste'),
    'KS': ('Kansas',               'Medio Oeste'),
    'KY': ('Kentucky',             'Sur'),
    'LA': ('Luisiana',             'Sur'),
    'ME': ('Maine',                'Noreste'),
    'MD': ('Maryland',             'Sur'),
    'MA': ('Massachusetts',        'Noreste'),
    'MI': ('Michigan',             'Medio Oeste'),
    'MN': ('Minnesota',            'Medio Oeste'),
    'MS': ('Misisipi',             'Sur'),
    'MO': ('Misuri',               'Medio Oeste'),
    'MT': ('Montana',              'Oeste'),
    'NE': ('Nebraska',             'Medio Oeste'),
    'NV': ('Nevada',               'Oeste'),
    'NH': ('Nueva Hampshire',      'Noreste'),
    'NJ': ('Nueva Jersey',         'Noreste'),
    'NM': ('Nuevo Mexico',         'Oeste'),
    'NY': ('Nueva York',           'Noreste'),
    'NC': ('Carolina del Norte',   'Sur'),
    'ND': ('Dakota del Norte',     'Medio Oeste'),
    'OH': ('Ohio',                 'Medio Oeste'),
    'OK': ('Oklahoma',             'Sur'),
    'OR': ('Oregon',               'Oeste'),
    'PA': ('Pensilvania',          'Noreste'),
    'PR': ('Puerto Rico',          'Sur'),
    'RI': ('Rhode Island',         'Noreste'),
    'SC': ('Carolina del Sur',     'Sur'),
    'SD': ('Dakota del Sur',       'Medio Oeste'),
    'TN': ('Tennessee',            'Sur'),
    'TX': ('Texas',                'Sur'),
    'UT': ('Utah',                 'Oeste'),
    'VT': ('Vermont',              'Noreste'),
    'VA': ('Virginia',             'Sur'),
    'WA': ('Washington',           'Oeste'),
    'WV': ('Virginia Occidental',  'Sur'),
    'WI': ('Wisconsin',            'Medio Oeste'),
    'WY': ('Wyoming',              'Oeste'),
}


# ==============================================================================
# BLOQUE DE EJECUCION
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("POBLACION DE CATALOGOS — INCENDIOS EE.UU. 1992-2015")
    print("=" * 70)

    poblar_origen_fuego()
    poblar_causas()
    poblar_clases_tamano()
    poblar_propiedad_terreno()
    poblar_calendario_estacional()

    print("-" * 70)
    print(f"Catalogos listos. Estados de referencia disponibles: {len(ESTADOS_EEUU)}")
    print("La dimension 'ubicacion' se construye durante el ETL (script 03).")
