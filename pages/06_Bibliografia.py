"""
pages/06_Bibliografia.py
================================================================================
REFERENCIAS BIBLIOGRAFICAS Y FUENTES CONSULTADAS
Origen del fuego: incendios antropicos vs. naturales, EE.UU. 1992-2015.
================================================================================
"""

import streamlit as st

st.set_page_config(page_title="Bibliografia", page_icon="📖", layout="wide")

st.title("Referencias bibliograficas")
st.caption("Fuentes de datos, literatura cientifica y documentacion tecnica consultada")

st.header("Fuente de datos primaria")
st.markdown("""
- Short, K. C. (2017). *Spatial wildfire occurrence data for the United States,
  1992-2015 [FPA_FOD_20170508]* (4.ª ed.). Fort Collins, CO: Forest Service Research
  Data Archive. https://doi.org/10.2737/RDS-2013-0009.4

- Tatman, R. (2020). *1.88 Million US Wildfires* [Conjunto de datos]. Kaggle.
  https://www.kaggle.com/datasets/rtatman/188-million-us-wildfires
""")

st.info("""
**Licencia y cita obligatoria.** El conjunto de datos se distribuye bajo licencia
**CC0 (dominio publico)**. Fue producido con financiamiento del Gobierno de Estados
Unidos y puede utilizarse sin permisos ni tarifas adicionales. La documentacion de
la fuente exige, no obstante, citar el trabajo de Short (2017) en toda publicacion,
presentacion o producto de investigacion que lo emplee. Esta investigacion cumple
dicho requisito.
""")

st.header("Literatura cientifica sobre el fenomeno")
st.markdown("""
- Balch, J. K., Bradley, B. A., Abatzoglou, J. T., Nagy, R. C., Fusco, E. J., y
  Mahood, A. L. (2017). Human-started wildfires expand the fire niche across the
  United States. *Proceedings of the National Academy of Sciences*, 114(11),
  2946-2951. https://doi.org/10.1073/pnas.1617394114

- Short, K. C. (2014). A spatial database of wildfires in the United States,
  1992-2011. *Earth System Science Data*, 6(1), 1-27.
  https://doi.org/10.5194/essd-6-1-2014

- Radeloff, V. C., Helmers, D. P., Kramer, H. A., Mockrin, M. H., Alexandre, P. M.,
  Bar-Massada, A., Butsic, V., Hawbaker, T. J., Martinuzzi, S., Syphard, A. D., y
  Stewart, S. I. (2018). Rapid growth of the US wildland-urban interface raises
  wildfire risk. *Proceedings of the National Academy of Sciences*, 115(13),
  3314-3319. https://doi.org/10.1073/pnas.1718850115
""")

st.header("Documentacion institucional y normativa")
st.markdown("""
- National Wildfire Coordinating Group. *NWCG Glossary of Wildland Fire*.
  https://www.nwcg.gov/glossary/a-z

- National Wildfire Coordinating Group. *Unit Identifier Program*.
  https://www.nwcg.gov/publications/pms931

- USDA Forest Service. *Fire Program Analysis (FPA)*.
  https://www.fs.usda.gov/managing-land/fire

- National Interagency Fire Center. *Statistics and Historical Data*.
  https://www.nifc.gov/fire-information/statistics
""")

st.header("Fundamentos metodologicos")
st.markdown("""
- Arias, F. G. (2012). *El proyecto de investigacion: introduccion a la metodologia
  cientifica* (6.ª ed.). Caracas: Editorial Episteme.

- Codd, E. F. (1970). A relational model of data for large shared data banks.
  *Communications of the ACM*, 13(6), 377-387. https://doi.org/10.1145/362384.362685

- Kimball, R., y Ross, M. (2013). *The Data Warehouse Toolkit: The Definitive Guide
  to Dimensional Modeling* (3.ª ed.). Indianapolis: John Wiley & Sons.
""")

st.header("Documentacion tecnica de las herramientas")
st.markdown("""
- DuckDB Foundation. *DuckDB Documentation*. https://duckdb.org/docs/

- Apache Software Foundation. *Apache Parquet Documentation*.
  https://parquet.apache.org/docs/

- Snowflake Inc. *Streamlit Documentation*. https://docs.streamlit.io/

- SQLite Consortium. *SQLite Documentation*. https://www.sqlite.org/docs.html

- Salesforce Inc. *Tableau Help*. https://help.tableau.com/current/pro/desktop/es-es/

- Plotly Technologies Inc. *Plotly Python Open Source Graphing Library*.
  https://plotly.com/python/
""")

st.markdown("---")
st.caption(
    "Escuela de Estadistica y Ciencias Actuariales · Universidad Central de Venezuela · "
    "Material academico de la asignatura Computacion II."
)
