# Guía de despliegue

Pasos para publicar en línea los dos productos de esta investigación: el aplicativo web
y el tablero. Ambos servicios exigen iniciar sesión con una cuenta personal, de modo que
estos pasos debe ejecutarlos el titular de la cuenta.

---

## 1. Aplicativo web en Streamlit Community Cloud

### Enlace directo con el formulario ya rellenado

<https://share.streamlit.io/deploy?repository=Olivertc24%2FAnalisis-Origen-de-los-Incendios-Forestales-en-Estados-Unidos-1992-2015-Grupo-2&branch=main&mainModule=app.py>

Ese enlace abre el formulario de despliegue con el repositorio, la rama y el archivo
principal ya seleccionados. Solo hay que iniciar sesión con GitHub y pulsar **Deploy**.

### Pasos manuales equivalentes

1. Entrar en <https://share.streamlit.io> e iniciar sesión con la cuenta de GitHub
   propietaria del repositorio.
2. Pulsar **Create app** → **Deploy a public app from GitHub**.
3. Rellenar el formulario:

   | Campo | Valor |
   |---|---|
   | Repository | `Olivertc24/Analisis-Origen-de-los-Incendios-Forestales-en-Estados-Unidos-1992-2015-Grupo-2` |
   | Branch | `main` |
   | Main file path | `app.py` |
   | App URL | el subdominio que se prefiera |

4. Pulsar **Deploy**. La primera construcción tarda unos minutos: la nube clona el
   repositorio e instala las dependencias de `requirements.txt`.

### Por qué el despliegue no debería fallar

El proyecto se preparó específicamente para este entorno:

- **No hay que subir datos aparte.** El Data Lake en Parquet está versionado en el
  repositorio (`data/`), de modo que el aplicativo es autocontenido. No depende de
  ningún servicio externo de almacenamiento ni de la base de 795 MB de Kaggle.
- **Las dependencias están verificadas.** Se instaló `requirements.txt` en un entorno
  limpio y se ejecutaron las siete páginas del aplicativo sin ningún error, con las
  versiones que la nube instalará: Streamlit 1.62, pandas 3.0.5, DuckDB 1.5.5,
  PyArrow 25.0.1, Plotly 7.0.0 y NumPy 2.5.2.
- **El repositorio es público**, requisito del plan gratuito de Community Cloud.
- **El consumo de memoria es bajo.** DuckDB consulta los archivos Parquet directamente
  desde disco en lugar de cargarlos en memoria, así que el aplicativo se mantiene
  holgadamente dentro del límite de recursos del plan gratuito pese a describir
  1.880.465 registros.

### Después de desplegar

Añadir la URL resultante al `README.md` principal, en la sección de puesta en marcha.

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
| Libro `.twb` armado | ⬜ Debe construirse en Tableau Desktop |

### Construcción del libro

La guía completa está en [`Tableau/README.md`](Tableau/README.md). En resumen:

1. Abrir **Tableau Public Desktop** (gratuito) o Tableau Desktop.
2. Conectar los tres archivos de `Tableau/extractos/` como fuentes de texto
   independientes. **No unirlas entre sí.**
3. Convertir en dimensión los campos numéricos que son códigos: `Anio`, `Mes` y `Orden de clase`.
   Sin este paso, Tableau sumaría los años en lugar de agruparlos.
4. Asignar los roles geográficos a `Estado` y, en el extracto de muestra, a `Latitud` y
   `Longitud`.
5. Crear los ocho campos calculados de
   [`Tableau/calculos/campos-calculados.md`](Tableau/calculos/campos-calculados.md).
   Todos son cocientes de sumas; ninguno usa `AVG()`, por la razón que ese documento
   explica con un ejemplo numérico.
6. Construir las doce hojas y los tres tableros según las tablas de
   [`Tableau/README.md`](Tableau/README.md).
7. Guardar como `Origen_del_Fuego_EEUU_1992_2015.twb` en la carpeta `Tableau/`.

Cada hoja de la especificación incluye **las cifras exactas que debe reproducir**, de
modo que el resultado es verificable contra el aplicativo de Streamlit.

### Publicación

1. En Tableau: **Servidor → Tableau Public → Guardar en Tableau Public**.
2. Iniciar sesión con la cuenta de Tableau Public (gratuita, se crea en
   <https://public.tableau.com>).
3. Al guardar, Tableau devuelve la URL pública del tablero.
4. Añadir esa URL al `README.md` principal y a `Tableau/README.md`.

> **Nota sobre los datos.** Tableau Public empaqueta los extractos dentro del libro
> publicado, de modo que el tablero funciona en línea sin necesidad de alojar los CSV
> en ningún otro sitio. El extracto principal de este proyecto (hechos_incendios.csv) está muy
> por debajo de los límites del servicio.

---

## Resumen

| Producto | Requisito | Acción |
|---|---|---|
| Aplicativo Streamlit | Cuenta de GitHub | Abrir el enlace directo de la sección 1 y pulsar *Deploy* |
| Tablero Tableau | Cuenta de Tableau Public | Construir el libro según la especificación y publicarlo |
