# Portfolio de Ingeniería de Datos

¡Hola! Soy **Andrea Monzón**, Ingeniera de Datos especializada en el diseño de arquitecturas distribuidas, automatización de pipelines ETL desatendidos y optimización avanzada de rendimiento en bases de datos relacionales orientadas a sistemas tributarios e impuestos.

Este repositorio centraliza casos de estudio y desarrollos de ingeniería de datos *end-to-end* enfocados en procesar grandes volúmenes de datos con máxima eficiencia, idempotencia y alta disponibilidad.

---

## Stack Tecnológico

| Categoría | Tecnologías |
| :--- | :--- |
| **Lenguajes** | Python (Pandas, Pytest, Requests), SQL, PL/SQL |
| **Big Data & Procesamiento** | Apache Spark (PySpark), Data Lakehouse Architectures |
| **Orquestación & Infraestructura** | Apache Airflow, Docker, Docker Compose |
| **Bases de Datos** | Oracle DB, SQL Server, DBLink |
| **Herramientas & Entorno** | Git, GitHub, VS Code, SQL Developer |

---

##  Proyectos y Casos de Estudio Destacados

### 1. ETL Distribuido con Apache Spark (`casos-estudios/ETL_SPARK`)
* **Descripción:** Pipeline de procesamiento masivo para el detalle de cuentas corrientes en administración tributaria. Reemplaza un proceso legacy basado en vistas Oracle por un procesamiento distribuido en PySpark.
* **Impacto & Métricas:**
  * Reducción del tiempo de carga de **4–6 horas a ~15 minutos** sobre un volumen de **110+ millones de filas**.
* **Decisiones Técnicas:**
  * **Lectura JDBC Paralela:** Particionamiento dinámico por columna de año (`ANIO`) y lectura por lotes configurable.
  * **Transformaciones Complejas:** Clasificación analítica de obligaciones corrientes y no corrientes (`_es_corriente`) comparadas contra fechas de vencimiento.
  * **Arquitectura Modular:** Separación estricta en `extract.py`, `transform.py` y `load.py` para testing modular.
* **🔗 Enlace:** [Ver proyecto ETL Spark](./casos-estudios/ETL_SPARK)

---

### 2. Orquestación ETL con Airflow & COMARB (`casos-estudios/ETL_Regimenes_COMARB`)
* **Descripción:** Pipeline containerizado en Docker y orquestado con Apache Airflow para la extracción, parseo, normalización e ingesta en Oracle DB de archivos de recaudación posicionales y delimitados de la Comisión Arbitral (SIRCAR, SIFERE, SIRCREB).
* **Impacto & Métricas:**
  * Automatización total de 3 procesos manuales independientes, reduciendo el tiempo por cierre de **30–45 min a < 2 min** desatendido.
* **Decisiones Técnicas:**
  * **Idempotencia por Hash (SHA-256):** Prevención de duplicados mediante trazabilidad en JSON local antes del procesamiento.
  * **Control de Flujo con Gatekeeper:** Validación de archivos de entrada con `AirflowSkipException` para evitar desperdicio de cómputo.
  * **Importaciones Diferidas:** Carga diferida de paquetes pesados en las tareas del DAG para evitar latencias en el Scheduler de Airflow.
* **🔗 Enlace:** [Ver proyecto ETL COMARB](./casos-estudios/ETL_Regimenes_COMARB)

---

### 3.Ingesta Incremental & Refactorización Analítica SQL (`sql/`)
* **Descripción:** Pipeline de ingesta incremental batcheada desde sistemas OLTP remotos vía DBLink, unificación de catálogos heterogéneos y refactorización analítica de declaraciones juradas e impuestos provinciales.
* **Impacto & Métricas:**
  * Reducción drástica del tiempo de procesamiento en tablas centrales de declaración jurada **de 2 días a ~15 minutos**.
  * Reducción de la complejidad algorítmica de $O(N^2)$ a $O(N \log N)$ en cálculos comparativos históricos MoM (Month-over-Month) y YoY (Year-over-Year).
* **Principios de Diseño & Logros Técnicos:**
  * **Single-Pass Engine (Query Tuning):** Eliminación de *self-joins* costosos y subconsultas correlacionadas escalares (`SELECT MAX(...)`) mediante CTEs y funciones analíticas de ventana (`ROW_NUMBER()`, `LAG()`).
  * **Ingesta Vectorizada en PL/SQL:** Procesamiento masivo con `BULK COLLECT INTO` (con `LIMIT 100`) para minimizar el *context switching* entre los motores PL/SQL y SQL, acompañado de *Batch Commit* cada 100 registros para evitar la saturación del espacio en Undo/Redo Tablespace.
  * **Data Quality & Fallback:** Unificación en cascada mediante `DECODE` para homogeneizar nomencladores impositivos (CUACM, NAECBA, NAES) y uso de `NULLIF(..., 0)` con `COUNT(*) OVER()` para prevenir excepciones de división por cero (ORA-01476).
* ** Enlace:** [Ver scripts y lógica SQL](./sql)

---

##Documentación Técnica

En la carpeta [docs/](./docs) encontrarás diagramas y detalles complementarios de la solución:
*  [`arquitectura.md`](./docs/arquitectura.md): Diagramas de flujo y topología de servicios.
*  [`DOCUMENTACION_TECNICA.md`](./docs/DOCUMENTACION_TECNICA.md): Especificaciones de los pipelines y esquemas de base de datos.

---

## Contacto

* **GitHub:** [@AndreaMonzon](https://github.com/AndreaMonzon)
