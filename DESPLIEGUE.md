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

## 2. Tablero en Tableau Public

### Estado actual

Lo que ya está listo y validado en este repositorio:

| Componente | Estado |
|---|---|
| Extractos de datos (`Tableau/extractos/`) | ✅ Generados, con control automático de consistencia contra el Data Lake |
| Script generador reproducible | ✅ `Tableau/generar_extractos.py` |
| Especificación del tablero hoja por hoja | ✅ `Tableau/README.md` |
| Campos calculados con su fórmula exacta | ✅ `Tableau/calculos/campos-calculados.md` |
| Registro de transformaciones | ✅ `Tableau/preparacion/transformacion-datos.md` |
| Libro `.twb` armado | ✅ `Tableau/Origen_del_Fuego_EEUU_1992_2015.twb` |

### El libro ya está construido

El archivo `Tableau/Origen_del_Fuego_EEUU_1992_2015.twb` se genera por código y quedó
verificado: se abre en Tableau Desktop y sus tres páginas renderizan sin errores.

Para regenerarlo (por ejemplo, tras cambiar los datos):

```bash
cd Tableau
python generar_extractos.py
python construir_libro.py
```

Páginas del tablero:

- **1. Panorama del origen**
- **2. Magnitud, causas y propiedad**
- **3. Geografia y evolucion**

### Publicación

1. Abrir `Tableau/Origen_del_Fuego_EEUU_1992_2015.twb` con **Tableau Public Desktop**
   (gratuito) o Tableau Desktop.
2. **Servidor → Tableau Public → Guardar en Tableau Public**.
3. Iniciar sesión con la cuenta de Tableau Public (gratuita, se crea en
   <https://public.tableau.com>).
4. Al guardar, Tableau devuelve la URL pública del tablero.
5. Añadir esa URL al `README.md` principal y a `Tableau/README.md`.

> **Nota sobre los datos.** Tableau Public empaqueta los extractos dentro del libro
> publicado, de modo que el tablero funciona en línea sin necesidad de alojar los CSV
> en ningún otro sitio. El extracto principal de este proyecto (hechos_incendios.csv) está muy
> por debajo de los límites del servicio.

---

## Resumen

| Producto | Requisito | Acción |
|---|---|---|
| Aplicativo Streamlit | — | ✅ Publicado en https://incendios-eeuu-grupo2.streamlit.app |
| Tablero Tableau | Cuenta de Tableau Público | Abrir `Tableau/Origen_del_Fuego_EEUU_1992_2015.twb` y usar *Servidor → Tableau Public → Guardar* |
