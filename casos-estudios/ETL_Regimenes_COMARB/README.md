# ETL Regímenes de Recaudación — SIRCAR / SIFERE / SIRCREB

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Apache Airflow](https://img.shields.io/badge/Airflow-2.8.1-red)
![Docker](https://img.shields.io/badge/Docker-Compose-blue)
![Oracle](https://img.shields.io/badge/Oracle-Database-red)

Pipeline ETL en Python **orquestado con Apache Airflow y Dockerizado**, que automatiza la extracción, normalización y carga de los archivos de recaudación enviados por la Comisión Arbitral (COMARB) hacia **Oracle**.

Antes: 3 procesos manuales independientes (unzip, parseo posicional a mano, armado de `.txt` concatenados, Si fallaba, había que empezar de cero, Riesgo alto de insertar doble ,Dependía del entorno local , ejecución de cargas por separado, ~30–45 min por cierre). 
Ahora: **un pipeline automático programado** que hace todo el flujo, con trazabilidad, idempotencia y alertas controladas,un tiempo de < 2 min (desatendido).

---

## Objetivo del proyecto

Demostrar un proceso ETL end-to-end en un contexto real de **Data Engineering**, aplicando buenas prácticas de infraestructura y orquestación:

1. **Extract** — tomar los `.zip` más recientes publicados por COMARB (desde una carpeta compartida en red) y copiarlos a un área de *staging*.
2. **Transform** — parsear archivos de **ancho fijo** (SIRCAR, SIRCREB) y **delimitados con comillas** (SIFERE), limpiar tipos, normalizar fechas (`YYYYMMDD`, `DD/MM/YYYY`), castear numéricos y concatenar por área.
3. **Load** — insertar en tablas Oracle (`pagos_sircreb`, `ACREDITACIONES_SIRCAR`, `ACREDITACIONES_SIFERE`) con `oracledb` en modo *thin* (sin dependencias de Instant Client).
4. **Orchestrate** — Apache Airflow gestiona el flujo (Gatekeeper -> Copia -> Carga) con reintentos y logs centralizados.

---

## Arquitectura (Airflow + Docker)

El proyecto corre sobre un clúster local de Airflow (CeleryExecutor) levantado con Docker Compose.

```text
F:\Tableau\Regimenes CM               (Carpeta de Red / Origen)
        │
        ▼ (Montaje / Sync)
┌─────────────────────────────────────────────────────────────┐
│  DOCKER COMPOSE (Airflow 2.8.1)                             │
│                                                             │
│  ┌──────────────┐     ┌──────────────────────────────────┐  │
│  │ Airflow DAG  │────►│ 1. gatekeeper_check_files        │  │
│  │ (Scheduler)  │     │    (Valida existencia de .zip)   │  │
│  └──────────────┘     └──────────────┬───────────────────┘  │
│                                      ▼                      │
│                       ┌──────────────────────────────────┐  │
│                       │ 2. prepare_and_copy_files        │  │
│                       │    (cp_archivos.py)              │  │
│                       │    - Busca el más reciente       │  │
│                       │    - Valida hash SHA-256         │  │
│                       │    - Copia a /staging            │  │
│                       └──────────────┬───────────────────┘  │
│                                      ▼                      │
│                       ┌──────────────────────────────────┐  │
│                       │ 3. load_etl_to_oracle            │  │
│                       │    (src/main.py)                 │  │
│                       │    - Parseo (parsers.py)         │  │
│                       │    - Concatenación (.txt)        │  │
│                       │    - Inserción (loaders.py)      │  │
│                       └──────────────┬───────────────────┘  │
│                                      ▼                      │
└──────────────────────────────────────┼──────────────────────┘
                                       ▼
                                  Oracle DB


Decision tecnica                             

Idempotencia por Hash (SHA-256): El script cp_archivos.py calcula el hash del archivo más reciente. Si ese hash ya fue procesado (guardado en un JSON local), la tarea se saltea. Esto evita insertar datos duplicados en Oracle si el pipeline se corre varias veces el mismo día.

Control de Flujo con Gatekeeper: La primera tarea del DAG (gatekeeper_check_files) valida que existan archivos en todas las carpetas requeridas. Si falta alguna, lanza un AirflowSkipException y no avanza, ahorrando tiempo de cómputo.

Airflow + Docker Aislado: Todo el entorno de ejecución está containerizado, garantizando que funcione igual en cualquier máquina.

Importaciones Diferidas en el DAG: Las importaciones de los módulos pesados (como pandas u oracledb) se hacen dentro de las funciones de las tareas, evitando que el Scheduler de Airflow colapse al intentar parsear el DAG.

Un solo connection pool reutilizado entre regímenes, configurado con try/finally para asegurar el cierre de conexiones incluso si falla la carga.

Parsers puros (funciones sin I/O) → fáciles de testear.

Archivado de procesados: Al terminar, los archivos se mueven a la carpeta procesados/, dejando el staging limpio para el próximo cierre mensual.


