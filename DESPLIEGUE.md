# Guía de despliegue

Pasos para publicar en línea los dos productos de esta investigación: el aplicativo web
y el tablero. Ambos servicios exigen iniciar sesión con una cuenta personal, de modo que
estos pasos debe ejecutarlos el titular de la cuenta.

---

## 1. Aplicativo web en Streamlit Community Cloud ✅ publicado

**https://incendios-eeuu-grupo2.streamlit.app**

El aplicativo está desplegado y funcionando. Se reconstruye solo con cada `push` a la
rama `main`.

### Configuración con la que se desplegó

| Campo | Valor |
|---|---|
| Repository | `Olivertc24/Analisis-Origen-de-los-Incendios-Forestales-en-Estados-Unidos-1992-2015-Grupo-2` |
| Branch | `main` |
| Main file path | `app.py` |
| App URL | `incendios-eeuu-grupo2` |

### Por qué el despliegue funcionó a la primera

- **No hubo que subir datos aparte.** El Data Lake en Parquet está versionado en el
  repositorio (`data/`), de modo que el aplicativo es autocontenido: no depende de
  ningún servicio externo de almacenamiento ni de la base de 795 MB de Kaggle.
- **Las dependencias estaban verificadas.** Antes de desplegar se instaló
  `requirements.txt` en un entorno limpio y se ejecutaron las siete páginas sin ningún
  error, con las versiones que instala la nube: Streamlit 1.62, pandas 3.0.5,
  DuckDB 1.5.5, PyArrow 25.0.1, Plotly 7.0.0 y NumPy 2.5.2.
- **El repositorio es público**, requisito del plan gratuito de Community Cloud.
- **El consumo de memoria es bajo.** DuckDB consulta los Parquet directamente desde
  disco en lugar de cargarlos en memoria, así que el aplicativo se mantiene dentro del
  límite de recursos del plan gratuito pese a describir 1.880.465 registros.

### Volver a desplegar o administrar la aplicación

Desde <https://share.streamlit.io> → *My apps*, el menú de la aplicación permite ver
los registros de construcción, reiniciarla o eliminarla.

---

## 2. Tablero en Tableau Public ✅ publicado

**https://public.tableau.com/app/profile/oliver.triveno/viz/Origen_del_Fuego_EEUU_1992_2015/1_Panoramadelorigen**


### Estado de los componentes en este repositorio

| Componente | Estado |
|---|---|
| Extractos de datos (`Tableau/extractos/`) | ✅ Generados, con control automático de consistencia contra el Data Lake |
| Scripts generadores reproducibles | ✅ Los cuatro de `Tableau/` |
| Especificación del tablero hoja por hoja | ✅ `Tableau/README.md` |
| Campos calculados con su fórmula exacta | ✅ `Tableau/calculos/campos-calculados.md` |
| Registro de transformaciones | ✅ `Tableau/preparacion/transformacion-datos.md` |
| Extracción `.hyper` | ✅ Se reconstruye con `construir_hyper.py` y viaja dentro del `.twbx` |
| Libro `.twb` | ✅ `Tableau/Origen_del_Fuego_EEUU_1992_2015.twb` |
| Paquete `.twbx` publicable | ✅ `Tableau/Origen_del_Fuego_EEUU_1992_2015.twbx` |
| Captura de la página 1 | ✅ `Tableau/capturas/1-panorama-del-origen.png` |
| Captura de la página 2 | ✅ `Tableau/capturas/2-magnitud-causas-y-propiedad.png` |
| Captura de la página 3 | ✅ `Tableau/capturas/3-geografia-y-evolucion.png` |

### Por qué hace falta el `.twbx` y no basta el `.twb`

Tableau Public **sólo publica libros cuyas fuentes de datos sean extracciones**. Un libro
conectado en vivo a archivos CSV se abre sin problema en Tableau Desktop, pero al
intentar guardarlo en Tableau Public devuelve:

> Los libros de trabajo guardados en Tableau Public deben usar extracciones. La fuente de
> datos `<nombre>` no es una extracción.

Por eso la cadena incluye dos pasos que no serían necesarios para un uso local:
`construir_hyper.py`, que convierte los CSV en una extracción `.hyper`, y
`empaquetar.py`, que envuelve libro y extracción en un `.twbx` portable.

### Regenerar el tablero

El libro se genera por código: `construir_libro.py` escribe el `.twb` entero a partir de
los extractos. Para rehacerlo tras un cambio en los datos:

```bash
cd Tableau
python generar_extractos.py    # CSV agregados desde el Data Lake
python construir_hyper.py      # CSV -> extracción .hyper
python construir_libro.py      # libro .twb sobre la extracción
python empaquetar.py           # .twbx portable, listo para publicar
```

El orden importa: cada script consume la salida del anterior.

Páginas del tablero:

- **1. Panorama del origen**
- **2. Magnitud, causas y propiedad**
- **3. Geografía y evolución**

### Cómo se publicó

1. Abrir `Tableau/Origen_del_Fuego_EEUU_1992_2015.twbx` con **Tableau Public Desktop** (gratuito).
2. **Archivo → Guardar en Tableau Public como...**
3. Iniciar sesión con la cuenta de Tableau Public (gratuita, se crea en
   <https://public.tableau.com>).
4. Al guardar, Tableau devuelve la URL pública del tablero, que es la que encabeza esta
   sección y el `README.md` principal.

> **Nota sobre los datos.** Tableau Public empaqueta la extracción dentro del libro
> publicado, de modo que el tablero funciona en línea sin necesidad de alojar los CSV en
> ningún otro sitio. La extracción de este proyecto está muy por debajo de los límites
> del servicio.

---

## Resumen

| Producto | Requisito | Acción |
|---|---|---|
| Aplicativo Streamlit | — | ✅ Publicado en https://incendios-eeuu-grupo2.streamlit.app |
| Tablero Tableau | — | ✅ Publicado en [Tableau Public](https://public.tableau.com/app/profile/oliver.triveno/viz/Origen_del_Fuego_EEUU_1992_2015/1_Panoramadelorigen) |
