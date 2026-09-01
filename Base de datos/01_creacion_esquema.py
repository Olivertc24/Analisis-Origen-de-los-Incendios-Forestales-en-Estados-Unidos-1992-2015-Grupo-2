"""
01_creacion_esquema.py
================================================================================
CREACION DEL ESQUEMA NORMALIZADO — INCENDIOS FORESTALES DE ESTADOS UNIDOS
Investigacion: Origen del fuego (antropico vs. natural), periodo 1992-2015.
Escuela de Estadistica y Ciencias Actuariales (EECA-UCV) — Computacion II
================================================================================

PROPOSITO
---------
La base original descargada de Kaggle (FPA_FOD_20170508.sqlite) es una tabla
unica y completamente desnormalizada: 39 columnas donde conviven identificadores,
descripciones textuales repetidas millones de veces y atributos geograficos.
Esa estructura es adecuada para *distribuir* el dato, pero no para *analizarlo*:

    * Redundancia: la cadena 'Debris Burning' se almacena 429.028 veces.
    * Anomalias de actualizacion: si una descripcion cambia, hay que tocar
      cientos de miles de filas.
    * Consultas lentas: agrupar por texto largo es mas costoso que agrupar por
      un entero de catalogo.

Este script construye un ESQUEMA EN ESTRELLA (star schema) normalizado hasta la
Tercera Forma Normal (3FN) sobre una base SQLite nueva. El modelo separa:

    - DIMENSIONES (catalogos pequenos, casi estaticos): origen del fuego, causa
      estadistica, clase de tamano, propiedad del terreno, ubicacion y
      calendario estacional.
    - HECHOS (tablas grandes, una fila por incendio): el registro del evento y
      su magnitud fisica.

DECISION DE DISENO: DOS TABLAS DE HECHOS 1:1
--------------------------------------------
Se separo `registro_incendios` (el "cuando, donde y por que") de
`magnitud_incendio` (el "cuanto ardio"). Ambas comparten la misma llave primaria
(fire_id), es decir mantienen una relacion 1:1. La razon es analitica y de
rendimiento: la mayoria de las consultas de la investigacion son o bien
temporales/geograficas o bien de magnitud, rara vez ambas al mismo tiempo. Al
separarlas, el motor columnar (Parquet + DuckDB) lee menos bytes por consulta.

ORDEN DE EJECUCION
------------------
Este script debe correrse PRIMERO, antes de poblar catalogos y antes del ETL,
porque las llaves foraneas exigen que las tablas referenciadas ya existan.
"""

import sqlite3 as sql
import os

# Nombre de la base de datos normalizada que produce esta investigacion.
# Se mantiene en la raiz del proyecto para que los scripts posteriores la
# encuentren con una ruta relativa simple.
DB_DESTINO = 'incendios_eeuu_1992_2015.db'


def abrir_conexion():
    """
    Devuelve una conexion a la base normalizada con las llaves foraneas activas.

    SQLite NO valida llaves foraneas por defecto (por retrocompatibilidad
    historica). Hay que activarlas explicitamente en CADA conexion con el
    PRAGMA correspondiente, de lo contrario las restricciones declaradas en el
    CREATE TABLE quedarian como simple documentacion decorativa.
    """
    conn = sql.connect(DB_DESTINO)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ==============================================================================
# BLOQUE 1 — TABLAS DE DIMENSION (CATALOGOS)
# ==============================================================================

def crear_dimension_origen_fuego():
    """
    Dimension raiz de la investigacion: clasifica el origen del fuego.

    Es la variable segmentadora del estudio. Agrupa las 13 causas estadisticas
    del estandar NWCG en tres categorias mutuamente excluyentes y exhaustivas:
    Antropico, Natural y No determinado. Se modela como tabla propia (y no como
    una simple columna de texto) porque de ella cuelga toda la comparacion.
    """
    conn = abrir_conexion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS origen_fuego (
            origen_id    INTEGER PRIMARY KEY,
            descripcion  TEXT NOT NULL UNIQUE,   -- Antropico / Natural / No determinado
            naturaleza   TEXT NOT NULL,          -- Evitable / No evitable / Indeterminada
            definicion   TEXT NOT NULL           -- Criterio operativo de clasificacion
        )
    """)
    conn.commit()
    conn.close()
    print("[OK] Dimension 'origen_fuego' creada.")


def crear_dimension_causas():
    """
    Catalogo de las 13 causas estadisticas (STAT_CAUSE) del estandar NWCG.

    Cada causa pertenece a un unico origen: la dependencia funcional
    causa -> origen se resuelve aqui mediante la FK origen_id, lo que evita
    almacenar el origen en la tabla de hechos (esto es precisamente lo que
    exige la Tercera Forma Normal: ningun atributo no clave puede depender de
    otro atributo no clave dentro de la tabla de hechos).
    """
    conn = abrir_conexion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS causas (
            cause_id         INTEGER PRIMARY KEY,   -- STAT_CAUSE_CODE original (1-13)
            descripcion_en   TEXT NOT NULL,         -- Etiqueta oficial en ingles
            descripcion_es   TEXT NOT NULL,         -- Traduccion documentada
            origen_id        INTEGER NOT NULL,
            FOREIGN KEY (origen_id) REFERENCES origen_fuego(origen_id)
        )
    """)
    conn.commit()
    conn.close()
    print("[OK] Dimension 'causas' creada.")


def crear_dimension_clases_tamano():
    """
    Catalogo de clases de tamano NWCG (A hasta G).

    Se conservan los limites numericos como columnas propias para que el
    aplicativo pueda validar la coherencia entre FIRE_SIZE y FIRE_SIZE_CLASS
    sin recurrir a constantes escritas en el codigo (regla de negocio en el
    dato, no en la aplicacion).
    """
    conn = abrir_conexion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS clases_tamano (
            class_id     INTEGER PRIMARY KEY,
            letra        TEXT NOT NULL UNIQUE,  -- A, B, C, D, E, F, G
            limite_inf   REAL NOT NULL,         -- Acres, cota inferior
            limite_sup   REAL,                  -- Acres, cota superior (NULL = sin tope)
            descripcion  TEXT NOT NULL,
            orden        INTEGER NOT NULL       -- Para ordenar en graficos (1..7)
        )
    """)
    conn.commit()
    conn.close()
    print("[OK] Dimension 'clases_tamano' creada.")


def crear_dimension_propiedad_terreno():
    """
    Catalogo del propietario o gestor del terreno en el punto de origen.

    Se anade la columna 'sector', que agrupa los 16 valores originales en
    macrocategorias (Federal, Estatal, Privado, Tribal, Local, No especificado).
    Esta jerarquia permite un analisis de dos niveles sin recodificar en cada
    consulta.
    """
    conn = abrir_conexion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS propiedad_terreno (
            owner_id     INTEGER PRIMARY KEY,   -- OWNER_CODE original
            descripcion  TEXT NOT NULL,
            sector       TEXT NOT NULL          -- Jerarquia superior del propietario
        )
    """)
    conn.commit()
    conn.close()
    print("[OK] Dimension 'propiedad_terreno' creada.")


def crear_dimension_ubicacion():
    """
    Dimension geografica a nivel estado-condado.

    En la fuente original, STATE, COUNTY, FIPS_CODE y FIPS_NAME viajan repetidos
    en cada una de los 1.88 millones de filas. Aqui se extrae la combinacion
    unica estado-condado a una dimension propia, y la tabla de hechos solo
    guarda un entero (location_id).

    La clave natural de la dimension es el par (state_code, fips_code) y NO el
    nombre del condado. El motivo es que el campo COUNTY de la fuente es texto
    libre, con multiples grafias para un mismo condado; el codigo FIPS, en
    cambio, es un identificador estable. El nombre se conserva unicamente como
    etiqueta de presentacion.

    Se agrega 'region_censo': las cuatro grandes regiones de la Oficina del
    Censo de EE.UU. (Noreste, Medio Oeste, Sur, Oeste), que permiten leer los
    patrones de origen del fuego a escala macro-regional.
    """
    conn = abrir_conexion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ubicacion (
            location_id    INTEGER PRIMARY KEY AUTOINCREMENT,
            state_code     TEXT NOT NULL,   -- Codigo de dos letras (CA, TX, ...)
            state_name     TEXT NOT NULL,   -- Nombre completo del estado
            region_censo   TEXT NOT NULL,   -- Noreste / Medio Oeste / Sur / Oeste
            county_name    TEXT,            -- Etiqueta del condado (NULL si la fuente no la reporta)
            fips_code      TEXT,            -- Codigo FIPS de tres digitos: identifica al condado
            UNIQUE (state_code, fips_code)
        )
    """)
    conn.commit()
    conn.close()
    print("[OK] Dimension 'ubicacion' creada.")


def crear_dimension_calendario():
    """
    Dimension de calendario estacional (12 filas, una por mes).

    La estacionalidad es uno de los ejes centrales de la investigacion: la
    hipotesis descriptiva es que el fuego antropico y el natural ocupan
    ventanas distintas del ano. Modelar el mes como dimension (y no derivarlo
    en cada consulta) permite adjuntar atributos estacionales estables
    (estacion del ano, temporada operativa de incendios) sin recalcularlos.
    """
    conn = abrir_conexion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS calendario_estacional (
            mes             INTEGER PRIMARY KEY,  -- 1..12
            nombre_mes      TEXT NOT NULL,
            abreviatura     TEXT NOT NULL,
            estacion        TEXT NOT NULL,        -- Invierno / Primavera / Verano / Otono
            temporada_fuego TEXT NOT NULL         -- Baja / Media / Alta (temporada operativa)
        )
    """)
    conn.commit()
    conn.close()
    print("[OK] Dimension 'calendario_estacional' creada.")


# ==============================================================================
# BLOQUE 2 — TABLAS DE HECHOS
# ==============================================================================

def crear_hechos_registro_incendios():
    """
    Tabla de hechos principal: un registro por incendio detectado.

    Responde al 'cuando, donde y por que'. Todas las descripciones textuales
    fueron sustituidas por llaves foraneas hacia los catalogos. Las coordenadas
    se conservan como atributos de la propia medicion (son propias del evento,
    no de una dimension: dos incendios del mismo condado tienen coordenadas
    distintas).
    """
    conn = abrir_conexion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS registro_incendios (
            fire_id          INTEGER PRIMARY KEY,   -- Llave subrogada correlativa del proyecto
            fod_id           INTEGER NOT NULL,      -- FOD_ID: trazabilidad con la fuente original
            fire_year        INTEGER NOT NULL,
            discovery_date   DATE NOT NULL,         -- Fecha de deteccion (YYYY-MM-DD)
            discovery_doy    INTEGER NOT NULL,      -- Dia juliano del ano (1-366)
            discovery_month  INTEGER NOT NULL,      -- FK al calendario estacional
            discovery_time   TEXT,                  -- Hora HHMM (NULL en ~47% de los casos)
            cause_id         INTEGER NOT NULL,
            location_id      INTEGER NOT NULL,
            owner_id         INTEGER NOT NULL,
            latitude         REAL NOT NULL,
            longitude        REAL NOT NULL,
            FOREIGN KEY (discovery_month) REFERENCES calendario_estacional(mes),
            FOREIGN KEY (cause_id)        REFERENCES causas(cause_id),
            FOREIGN KEY (location_id)     REFERENCES ubicacion(location_id),
            FOREIGN KEY (owner_id)        REFERENCES propiedad_terreno(owner_id)
        )
    """)
    conn.commit()
    conn.close()
    print("[OK] Tabla de hechos 'registro_incendios' creada.")


def crear_hechos_magnitud_incendio():
    """
    Tabla de hechos de magnitud: un registro por incendio, relacion 1:1.

    Responde al 'cuanto ardio'. Ademas de la superficie original en acres se
    precalculan dos campos derivados:

        * superficie_ha: conversion a hectareas (1 acre = 0,40468564224 ha),
          util para contrastar con literatura internacional.
        * es_gran_incendio: bandera 1/0 que marca las clases F y G (>= 1.000
          acres). En la literatura de manejo del fuego estas son las
          'large fires' que concentran la mayor parte de la superficie quemada.

    Precalcular estos campos en el ETL (y no en cada consulta) es una decision
    de rendimiento: se paga una sola vez el costo del calculo sobre 1,88
    millones de filas.
    """
    conn = abrir_conexion()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS magnitud_incendio (
            fire_id          INTEGER PRIMARY KEY,   -- Relacion 1:1 con registro_incendios
            class_id         INTEGER NOT NULL,
            superficie_acres REAL NOT NULL,
            superficie_ha    REAL NOT NULL,
            es_gran_incendio INTEGER NOT NULL,      -- 1 = clases F o G
            FOREIGN KEY (fire_id)  REFERENCES registro_incendios(fire_id),
            FOREIGN KEY (class_id) REFERENCES clases_tamano(class_id)
        )
    """)
    conn.commit()
    conn.close()
    print("[OK] Tabla de hechos 'magnitud_incendio' creada.")


# ==============================================================================
# BLOQUE 3 — INDICES DE APOYO
# ==============================================================================

def crear_indices():
    """
    Indices sobre las llaves foraneas y sobre los campos mas filtrados.

    SQLite crea automaticamente indices para las llaves PRIMARIAS, pero no para
    las foraneas. Sin estos indices, cada JOIN de la aplicacion degeneraria en
    un recorrido completo de 1,88 millones de filas.
    """
    conn = abrir_conexion()
    indices = [
        "CREATE INDEX IF NOT EXISTS idx_reg_causa    ON registro_incendios(cause_id)",
        "CREATE INDEX IF NOT EXISTS idx_reg_ubic     ON registro_incendios(location_id)",
        "CREATE INDEX IF NOT EXISTS idx_reg_owner    ON registro_incendios(owner_id)",
        "CREATE INDEX IF NOT EXISTS idx_reg_anio     ON registro_incendios(fire_year)",
        "CREATE INDEX IF NOT EXISTS idx_reg_mes      ON registro_incendios(discovery_month)",
        "CREATE INDEX IF NOT EXISTS idx_mag_clase    ON magnitud_incendio(class_id)",
    ]
    for sentencia in indices:
        conn.execute(sentencia)
    conn.commit()
    conn.close()
    print("[OK] Indices de apoyo creados.")


# ==============================================================================
# BLOQUE DE EJECUCION
# ==============================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("CREACION DEL ESQUEMA NORMALIZADO — INCENDIOS EE.UU. 1992-2015")
    print("=" * 70)

    # 1. Primero las dimensiones: las llaves foraneas de los hechos las exigen.
    crear_dimension_origen_fuego()
    crear_dimension_causas()
    crear_dimension_clases_tamano()
    crear_dimension_propiedad_terreno()
    crear_dimension_ubicacion()
    crear_dimension_calendario()

    # 2. Luego las tablas de hechos.
    crear_hechos_registro_incendios()
    crear_hechos_magnitud_incendio()

    # 3. Finalmente los indices.
    crear_indices()

    print("-" * 70)
    print(f"Esquema disponible en: {os.path.abspath(DB_DESTINO)}")
