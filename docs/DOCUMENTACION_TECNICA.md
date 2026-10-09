# 🏛️ Documentación Técnica de la Arquitectura de Datos

## 1. Fuente OLTP Remota
* **Tecnología:** Oracle Database distante conectada mediante `DBLink` (`@tcsprod`).
* **Origen:** Tabla transaccional `ddjj_para_procesar` que registra las declaraciones juradas pendientes de procesamiento (`procesada = 'N'`) filtrando por impuesto (`0035`) y concepto (`0017`).

---

## 2. Capa de Ingesta Incremental (PL/SQL)
* **Componente:** Stored Procedure `analitic.carga_detalledjib_incre_v2`.
* **Procesamiento Vectorizado (Bulk Collect):** Utiliza cursores explícitos con `BULK COLLECT INTO` y parámetro `LIMIT 100` para reducir el intercambio de contexto (*Context Switching*) entre los motores PL/SQL y SQL.
* **Control de Transacciones (Batch Commit):** Ejecuta `COMMIT` por cada lote de 100 registros procesados, previniendo el desbordamiento del *Undo Tablespace* en cargas masivas sobre redes o DBLinks.
* **Idempotencia:** Verifica previamente si la cantidad de registros en origen coincide con el destino antes de insertar o reemplazar filas inconsistentes.

---

## 3. Data Warehouse / Staging
* **Tabla Staging:** `analitic.detalle_dj` almacena los registros crudos procesados.
* **Vista de Unificación:** `VW_DETALLE_DJ_AGREGADO` estandariza catálogos heterogéneos de actividades económicas (`CUACM`, `NAECBA`, `NAES`) aplicando expresiones `DECODE` en cascada.
* **Integridad Numérica:** Calcula métricas divididas (`imp_div`, `base_imponible_div`) utilizando `COUNT(*) OVER()` para prevenir sobreconteos (*Fan-out Effect*) y `NULLIF(..., 0)` para mitigar errores de división por cero.

---

## 4. Capa Analítica & Query Tuning (Single-Pass Engine)
* **Desduplicación:** Implementa `ROW_NUMBER() OVER(PARTITION BY ... ORDER BY numero_rectificativa DESC)` reteniendo únicamente la última versión presentada (`rn_rect = 1`).
* **Comparativas Temporales:** Calcula métricas comparativas MoM ($t-1$) y YoY ($t-12$) mediante la función analítica `LAG()` en un único escaneo (*Single-Pass*) sobre la tabla base, eliminando *Self-Joins* e iteraciones $O(N^2)$.
* **Indicadores de Cumplimiento:** Evalúa el cumplimiento en término ajustando la fecha de presentación contra el último día del mes/año de vencimiento (`corriente_mes`, `corriente_anio`).