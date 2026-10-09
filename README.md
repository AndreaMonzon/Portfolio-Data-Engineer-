 Logros Técnicos y Principios de Diseño

1. Refactorización Analítica & Query Tuning (Single-Pass Engine)Problema Original: El modelo previo utilizaba Self-Joins costosos ($O(N^2)$) sumando desplazamientos de período (anticipo + 100) y subconsultas correlacionadas escalares (SELECT MAX(...)) ejecutadas iterativamente por cada fila.Solución Aplicada: 
Reescritura completa mediante Expresiones de Tabla Comunes (WITH CTEs) y funciones analíticas de ventana (ROW_NUMBER() y LAG()).
Resultado: Cálculo simulado de comparativas $t-1$ (MoM) y $t-12$ (YoY) en una sola pasada (Single-Pass) sobre la tabla base, reduciendo la complejidad algorítmica de $O(N^2)$ a $O(N \log N)$ y disminuyendo las lecturas de bloque de disco.

3. Ingesta Incremental Vectorizada & Batch Commit (PL/SQL)Procesamiento por Lotes: Reemplazo de bucles row-by-row por lectura y procesamiento vectorizado con BULK COLLECT INTO y parámetro LIMIT 100, minimizando el choque térmico (Context Switching) entre los motores PL/SQL y SQL.

Mapeo de Transacciones: Gestión de transacciones con Batch Commit cada 100 registros para evitar el agotamiento del área de Undo/Redo Tablespace en ejecuciones masivas sobre DBLink.

Idempotencia y Reconciliación: Verificación previa de paridad de registros entre origen y destino antes de la actualización de estado a 'C' (Completado).


3. Normalización y Calidad de Datos (Data Quality)Unificación de Catálogos: Estrategia de búsqueda en cascada (Fallback) mediante expresiones DECODE para mapear equivalencias entre nomencladores impositivos (CUACM, NAECBA y NAES).
4. Protección de Métricas: Uso de COUNT(*) OVER() analítico y la función NULLIF(..., 0) para prorratear bases imponibles e impuestos evitando excepciones por división por cero (ORA-01476).


Reglas de Negocio: Clasificación automática del nivel de cumplimiento en la presentación de declaraciones juradas dentro del mes o año fiscal correspondiente (corriente_mes, corriente_anio).



#  Pipeline de Ingesta Incremental y Optimización Analítica en Oracle SQL

##  Descripción del Proyecto
Este repositorio contiene la solución completa de **Data Engineering** desarrollada sobre **Oracle Database** para el procesamiento, estandarización y análisis de declaraciones juradas e impuestos provinciales.

La solución abarca desde la ingesta incremental batcheada de sistemas OLTP remotos vía `DBLink`, hasta la unificación de catálogos de actividades económicas heterogéneas y la refactorización de modelos analíticos históricos comparativos **MoM (Month-over-Month)** y **YoY (Year-over-Year)** reduciendo drásticamente el consumo de I/O en la base de datos.

---

##  Arquitectura de Datos

```mermaid
flowchart LR
    subgraph Fuentes ["1. Origen OLTP Remoto"]
        A[DBLink: @tcsprod<br/>ddjj_para_procesar]
    end

    subgraph Ingesta ["2. Ingesta Incremental"]
        B[PL/SQL Procedure<br/>BULK COLLECT + Batch Commit: 100]
    end

    subgraph DW ["3. Data Warehouse / Staging"]
        C[(analitic.detalle_dj)]
        D[Vista: VW_DETALLE_DJ_AGREGADO]
    end

    subgraph Analitica ["4. Capa Analítica & Tuning"]
        E[Single-Pass Engine<br/>ROW_NUMBER + LAG YoY/MoM]
        F[Reportes & Dashboards]
    end

    A -->|Lectura Batch| B
    B -->|Upsert / Sync| C
    C -->|Unificación NAES/CUACM| D
    D -->|Lectura Única / Window Functions| E
    E -->|Consumo Analítico| F
