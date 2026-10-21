# ETL Regímenes de Recaudación — SIRCAR / SIFERE / SIRCREB

Pipeline ETL en Python que **automatiza la extracción, normalización y carga** de los
archivos de recaudación que envía la Comisión Arbitral (COMARB) hacia **Oracle**.

Antes: 3 procesos manuales independientes (unzip, parseo posicional a mano, armado de
`.txt` concatenados, ejecución de cargas por separado, ~30–45 min por cierre).
Ahora: **un solo comando** que hace todo, con trazabilidad por etapa.

---

## Objetivo del proyecto

Demostrar un proceso ETL end-to-end en un contexto real de **Data Engineering**:

1. **Extract** — tomar los `.zip` más recientes publicados por COMARB
   (publicados en una carpeta compartida de Tableau).
2. **Transform** — parsear archivos de **ancho fijo** (SIRCAR, SIRCREB) y
   **delimitados con comillas** (SIFERE), limpiar tipos, normalizar fechas
   (`YYYYMMDD`, `DD/MM/YYYY`), castear numéricos y concatenar por área.
3. **Load** — insertar en tablas Oracle (`pagos_sircreb`, `ACREDITACIONES_SIRCAR`,
   `ACREDITACIONES_SIFERE`) con `oracledb`, commits al final de cada lote.

---

##  Arquitectura

```
F:\Tableau\Regimenes CM        ┌──────────────────────┐
 (SIFERE / SIRCAR / SIRCREB)   │   cp_archivos.py     │
        │                      │ (toma .zip más nuevo │
        ▼                      │  por subcarpeta)     │
   *.zip en carpeta local ────►└──────────┬───────────┘
                                          │
                                          ▼
                              ┌──────────────────────┐
                              │   src/main.py        │
                              │  (orquestador)       │
                              └──────────┬───────────┘
                                         │
         ┌───────────────────────────────┼───────────────────────────────┐
         ▼                               ▼                               ▼
   SIRCAR (posicional)            SIFERE (txt ;)                 SIRCREB (posicional)
   acreditaciones.txt             *.txt (skip 2 líneas)          pagos.txt
         │                               │                               │
         ▼                               ▼                               ▼
   parsers.py → ACREDITACIONES_SIRCAR   ACREDITACIONES_SIFERE   pagos_sircreb
                     └───────────────┐   │   ┌───────────────┘
                                     ▼   ▼   ▼
                                   Oracle DB
```

---

##  Datos de entrada

| Régimen | Archivo dentro del zip | Formato | Separador | Encabezado |
|---------|------------------------|---------|-----------|------------|
| SIRCAR  | `acreditaciones.txt`   | Ancho fijo | `;` (armado) | 1 línea |
| SIFERE  | `*.txt`                | Delimitado `;`, con `"` | `;` | 2 líneas |
| SIRCREB | `pagos.txt`            | Ancho fijo | `,` (armado) | 1 línea |

> Los archivos posicionales se reconstruyen por offsets fijos y se les antepone el
> `COD_AREA` (prefijo de 3 dígitos del nombre del `.zip`) para poder particionar
> los registros por área.

---

## Cómo ejecutarlo


# 1) Traer los .zip más recientes desde la carpeta compartida
python scripts/cp_archivos.py

# 2) Ejecutar el pipeline completo
python -m src.main
```

---

##  Decisiones técnicas destacadas

- **Un solo connection pool** reutilizado entre regímenes (antes: 3 conexiones
  separadas, 3 `init_oracle_client`).
- **Configuración centralizada** en `src/config.py`: rutas, tablas, offsets y
  columnas numéricas/fecha. Agregar un régimen nuevo = agregar una entrada al
  diccionario, sin tocar lógica.
- **Parsers puros** (funciones sin I/O) → fáciles de testear.
- **Idempotencia por etapa**: si falla la carga a Oracle, los `.txt` intermedios
  quedan disponibles en `Resultado/` para reprocesar sin volver a descomprimir.
- **`limpiar_txt()`** corre al final de cada régimen, evitando contaminar el
  siguiente ciclo (bug original: el `.txt` del régimen anterior podía confundirse
  con el actual).

---

##  Antes vs. Después

| Aspecto | Antes (manual) | Ahora |
|---|---|---|
| Ejecución | 3 scripts independientes, uno por régimen | `python -m src.main` |
| Extracción | Descomprimir a mano, arrastrar `.txt` | `cp_archivos.py` toma el `.zip` más nuevo |
| Transformación | Edición manual / plantillas Excel | Parsers declarativos (offsets en config) |
| Carga | SQL ejecutado por separado | `oracledb` con parámetros bindeados |
| Tiempo | ~30–45 min por cierre | **< 2 min** |
| Errores | Frecuentes (offset mal copiado, coma vs punto, fechas) | Validaciones y `try/except` por línea |
| Trazabilidad | Ninguna | Log de cada etapa + archivos intermedios en `Resultado/` |

---

## Próximos pasos (roadmap)

- [ ] Orquestación con **Airflow / Prefect** (DAG `etl_regimenes`).
- [ ] Tests unitarios de `parsers.py` con `pytest` y fixtures de muestra.
- [ ] Logging estructurado (`loguru` o `logging` con JSON).
- [ ] Carga por **staging table + MERGE** para hacerla idempotente.
- [ ] Dashboard en Tableau / Superset consumiendo las tablas Oracle.

---

##  Autor

**Andrea Monzón** — Data Engineer
 [GitHub](https://github.com/AndreaMonzon)