"""
generar_extractos.py
================================================================================
GENERACION DE LOS EXTRACTOS PARA EL TABLERO DE TABLEAU
Investigacion: Origen del fuego (antropico vs. natural), EE.UU. 1992-2015.
Escuela de Estadistica y Ciencias Actuariales (EECA-UCV) — Computacion II
================================================================================

POR QUE EXTRACTOS AGREGADOS Y NO EL DATO CRUDO
----------------------------------------------
Tableau podria conectarse directamente a los 1,88 millones de registros del Data
Lake. No se hace, por tres razones:

  1. RENDIMIENTO EN EL TABLERO. Cada interaccion del usuario (un filtro, un
     cambio de nivel) reevalua las consultas. Sobre 1,88 millones de filas eso
     introduce una latencia perceptible; sobre 245.653 filas agregadas, no.

  2. PORTABILIDAD. Un archivo CSV se abre en cualquier instalacion de Tableau,
     incluida Tableau Public, sin conectores adicionales ni controladores.

  3. GRANULARIDAD SUFICIENTE. El tablero nunca desciende al incendio individual:
     su unidad minima de lectura es la combinacion ano-mes-estado-causa-clase-
     sector. Agregar a ese nivel no pierde ninguna informacion que el tablero
     necesite.

ANCHURA DEL EXTRACTO
--------------------
El extracto conserva solo las columnas que el tablero usa. Se omiten
deliberadamente los atributos descriptivos redundantes (nombre completo del mes,
etiqueta original en ingles de la causa, rango textual de la clase, propietario
detallado): son cadenas largas que se repetirian en las 245.653 filas del archivo
y que el tablero no necesita, porque ya dispone del atributo corto equivalente.
Recortarlas redujo el archivo de 43,5 MB a menos de la mitad sin perder ninguna
capacidad de analisis.

LA REGLA DE ORO DE LA AGREGACION
--------------------------------
Los extractos almacenan SUMAS y CONTEOS, nunca PROMEDIOS.

El motivo es que el promedio de un conjunto de promedios NO es el promedio del
conjunto, salvo que todos los grupos tengan el mismo tamano. Si el extracto
guardara `acres_promedio` por fila, cualquier agregacion posterior en Tableau
—por estado, por ano, por origen— produciria un promedio no ponderado y por
tanto incorrecto.

Almacenando `n_incendios` y `acres`, Tableau reconstruye el promedio correcto en
cualquier nivel con `SUM([Acres]) / SUM([N Incendios])`. Esta es la razon por la
que los campos calculados del libro se definen como cocientes de sumas y no como
`AVG()` de una columna.

SALIDA
------
Tres archivos en la carpeta `extractos/`:
  * hechos_incendios.csv : tabla de hechos agregada (fuente principal)
  * focos_muestra.csv    : muestra de incendios individuales para el mapa de puntos
  * resumen_origen.csv   : cuadro comparativo por origen, para las tarjetas de KPI
"""

import os
import duckdb

# La carpeta de salida es relativa a la posicion de este script, de modo que el
# proceso funciona igual en cualquier equipo.
DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
DIRECTORIO_DATA = os.path.abspath(os.path.join(DIRECTORIO_BASE, "..", "data"))
DIRECTORIO_SALIDA = os.path.join(DIRECTORIO_BASE, "extractos")

# Tamano de la muestra para el mapa de puntos. Tableau dibuja marcas individuales
# y por encima de unas decenas de miles la representacion deja de ser legible
# ademas de lenta.
TAMANO_MUESTRA = 40_000

TABLAS = {
    "incendios":  "registro_incendios.parquet",
    "magnitud":   "magnitud_incendio.parquet",
    "causas":     "causas.parquet",
    "origen":     "origen_fuego.parquet",
    "clases":     "clases_tamano.parquet",
    "propiedad":  "propiedad_terreno.parquet",
    "ubicacion":  "ubicacion.parquet",
    "calendario": "calendario_estacional.parquet",
}


def abrir_conexion():
    """Monta el Data Lake en una conexion DuckDB en memoria."""
    con = duckdb.connect(database=":memory:")
    for nombre, archivo in TABLAS.items():
        ruta = os.path.join(DIRECTORIO_DATA, archivo)
        if not os.path.exists(ruta):
            raise FileNotFoundError(
                f"No se encontro {ruta}. Ejecute antes los scripts de 'Base de datos/'.")
        con.execute(f"CREATE OR REPLACE VIEW {nombre} AS "
                    f"SELECT * FROM read_parquet('{ruta}')")
    return con


def exportar(con, nombre_archivo, consulta):
    """Ejecuta una consulta y la escribe como CSV con encabezado."""
    ruta = os.path.join(DIRECTORIO_SALIDA, nombre_archivo)
    con.execute(f"COPY ({consulta}) TO '{ruta}' (HEADER, DELIMITER ',')")
    filas = con.execute(f"SELECT COUNT(*) FROM ({consulta})").fetchone()[0]
    peso = os.path.getsize(ruta) / 1024 / 1024
    print(f"   {nombre_archivo:<26} {filas:>9,} filas   {peso:>7.2f} MB")
    return filas


# ==============================================================================
# EXTRACTO 1 — TABLA DE HECHOS AGREGADA
# ==============================================================================

CONSULTA_HECHOS = """
    SELECT
        i.fire_year                     AS "Anio",
        cal.mes                         AS "Mes",
        cal.abreviatura                 AS "Mes abrev",
        cal.estacion                    AS "Estacion",
        cal.temporada_fuego             AS "Temporada de fuego",
        u.state_code                    AS "Codigo estado",
        u.state_name                    AS "Estado",
        u.region_censo                  AS "Region censal",
        o.descripcion                   AS "Origen del fuego",
        c.descripcion_es                AS "Causa",
        cl.letra                        AS "Clase de tamano",
        cl.orden                        AS "Orden de clase",
        p.sector                        AS "Sector de propiedad",
        -- Medidas: siempre sumas y conteos, nunca promedios.
        COUNT(*)                        AS "N incendios",
        ROUND(SUM(m.superficie_acres), 4)  AS "Acres",
        ROUND(SUM(m.superficie_ha), 4)     AS "Hectareas",
        SUM(m.es_gran_incendio)            AS "N grandes incendios"
    FROM incendios  i
    JOIN causas     c   ON i.cause_id        = c.cause_id
    JOIN origen     o   ON c.origen_id       = o.origen_id
    JOIN magnitud   m   ON i.fire_id         = m.fire_id
    JOIN clases     cl  ON m.class_id        = cl.class_id
    JOIN ubicacion  u   ON i.location_id     = u.location_id
    JOIN propiedad  p   ON i.owner_id        = p.owner_id
    JOIN calendario cal ON i.discovery_month = cal.mes
    GROUP BY ALL
"""

# ==============================================================================
# EXTRACTO 2 — MUESTRA DE FOCOS PARA EL MAPA DE PUNTOS
# ==============================================================================

# Se emplea ORDER BY random() LIMIT y no USING SAMPLE porque el optimizador de
# DuckDB empuja el muestreo hasta la lectura del archivo, tomando la muestra
# antes de aplicar las uniones y devolviendo muchas menos filas de las pedidas.
CONSULTA_MUESTRA = f"""
    SELECT
        i.latitude                      AS "Latitud",
        i.longitude                     AS "Longitud",
        i.fire_year                     AS "Anio",
        cal.abreviatura                 AS "Mes abrev",
        o.descripcion                   AS "Origen del fuego",
        c.descripcion_es                AS "Causa",
        u.state_name                    AS "Estado",
        cl.letra                        AS "Clase de tamano",
        ROUND(m.superficie_acres, 4)    AS "Acres",
        ROUND(LOG10(m.superficie_acres + 1) + 0.15, 4) AS "Peso logaritmico"
    FROM incendios  i
    JOIN causas     c   ON i.cause_id        = c.cause_id
    JOIN origen     o   ON c.origen_id       = o.origen_id
    JOIN magnitud   m   ON i.fire_id         = m.fire_id
    JOIN clases     cl  ON m.class_id        = cl.class_id
    JOIN ubicacion  u   ON i.location_id     = u.location_id
    JOIN calendario cal ON i.discovery_month = cal.mes
    ORDER BY random()
    LIMIT {TAMANO_MUESTRA}
"""

# ==============================================================================
# EXTRACTO 3 — CUADRO COMPARATIVO POR ORIGEN
# ==============================================================================

CONSULTA_RESUMEN = """
    WITH totales AS (
        SELECT COUNT(*) AS n_total, SUM(m2.superficie_acres) AS acres_total
        FROM incendios i2 JOIN magnitud m2 ON i2.fire_id = m2.fire_id
    )
    SELECT
        o.descripcion                                            AS "Origen del fuego",
        o.naturaleza                                             AS "Naturaleza",
        COUNT(*)                                                 AS "N incendios",
        ROUND(COUNT(*) * 100.0 / MAX(t.n_total), 4)              AS "Pct incendios",
        ROUND(SUM(m.superficie_acres), 2)                        AS "Acres",
        ROUND(SUM(m.superficie_acres) * 100.0 / MAX(t.acres_total), 4)
                                                                 AS "Pct acres",
        ROUND(AVG(m.superficie_acres), 4)                        AS "Acres promedio",
        ROUND(MEDIAN(m.superficie_acres), 4)                     AS "Acres mediana",
        ROUND(STDDEV_POP(m.superficie_acres), 4)                 AS "Desviacion tipica",
        ROUND(SKEWNESS(m.superficie_acres), 4)                   AS "Asimetria"
    FROM incendios i
    JOIN causas    c ON i.cause_id  = c.cause_id
    JOIN origen    o ON c.origen_id = o.origen_id
    JOIN magnitud  m ON i.fire_id   = m.fire_id
    CROSS JOIN totales t
    GROUP BY o.descripcion, o.naturaleza
    ORDER BY "N incendios" DESC
"""


# ==============================================================================
# BLOQUE DE EJECUCION
# ==============================================================================
if __name__ == "__main__":
    print("=" * 62)
    print("GENERACION DE EXTRACTOS PARA TABLEAU")
    print("=" * 62)

    os.makedirs(DIRECTORIO_SALIDA, exist_ok=True)
    conexion = abrir_conexion()

    print(f"{'ARCHIVO':<26}{'FILAS':>12}{'TAMANO':>12}")
    print("-" * 62)
    exportar(conexion, "hechos_incendios.csv", CONSULTA_HECHOS)
    exportar(conexion, "focos_muestra.csv", CONSULTA_MUESTRA)
    exportar(conexion, "resumen_origen.csv", CONSULTA_RESUMEN)
    print("-" * 62)

    # Control de consistencia: el extracto agregado debe reproducir exactamente
    # los totales del Data Lake. Si no lo hiciera, el tablero mostraria cifras
    # distintas a las del aplicativo.
    control = conexion.execute("""
        SELECT COUNT(*) AS n, ROUND(SUM(m.superficie_acres), 2) AS acres
        FROM incendios i JOIN magnitud m ON i.fire_id = m.fire_id
    """).fetchone()
    agregado = conexion.execute(f"""
        SELECT SUM("N incendios"), ROUND(SUM("Acres"), 2) FROM ({CONSULTA_HECHOS})
    """).fetchone()

    print("CONTROL DE CONSISTENCIA")
    print(f"   Incendios en el Data Lake : {control[0]:>15,}")
    print(f"   Incendios en el extracto  : {agregado[0]:>15,}")
    print(f"   Acres en el Data Lake     : {control[1]:>15,.2f}")
    print(f"   Acres en el extracto      : {agregado[1]:>15,.2f}")
    coincide = (control[0] == agregado[0]) and (abs(control[1] - agregado[1]) < 1)
    print(f"   Resultado                 : {'COINCIDEN' if coincide else 'DISCREPANCIA'}")

    conexion.close()
