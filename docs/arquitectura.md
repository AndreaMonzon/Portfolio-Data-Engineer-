flowchart TD
    %% Nodos de la Fuente
    subgraph S1 ["1. Fuente OLTP Remota"]
        A[("Oracle OLTP<br/>@tcsprod")]
        A1["ddjj_para_procesar<br/>(procesada = 'N')"]
        A --- A1
    end

    %% Nodos de Ingesta / ETL
    subgraph S2 ["2. Capa de Ingesta Incremental"]
        B["Procedure PL/SQL<br/>carga_detalledjib_incre_v2"]
        B1["Cursor & Bulk Collect<br/>LIMIT 100"]
        B2["Reconciliación Origen-Destino<br/>(COUNT Verification)"]
        B3["Batch Commit<br/>(Control Undo/Redo)"]
        B --> B1 --> B2 --> B3
    end

    %% Nodos de Staging / Data Warehouse
    subgraph S3 ["3. Data Warehouse / Staging"]
        C[("Tabla Staging<br/>analitic.detalle_dj")]
        D["Vista de Unificación<br/>VW_DETALLE_DJ_AGREGADO"]
        D1["Mapeo Fallback DECODE<br/>(CUACM / NAECBA / NAES)"]
        D2["Prorrateo & Control Error 0<br/>(NULLIF + Window Count)"]
        C --> D
        D --- D1
        D --- D2
    end

    %% Nodos Analíticos
    subgraph S4 ["4. Capa Analítica & Query Tuning"]
        E["Single-Pass Engine<br/>sql/02_pipeline_analitico_yoy.sql"]
        E1["Filtro Desduplicador<br/>ROW_NUMBER() DESC = 1"]
        E2["Comparativas MoM & YoY<br/>LAG(..., 1) & LAG(..., 12)"]
        E3["Reglas de Cumplimiento<br/>corriente_mes / corriente_anio"]
        E --> E1 --> E2 --> E3
    end

    %% Consumo
    subgraph S5 ["5. Consumo"]
        F["Reportes Impositivos / Dashboards"]
    end

    %% Conexiones principales
    A1 -->|DBLink| B
    B3 -->|Insert / Sync| C
    D -->|Single-Pass Scan| E
    E3 -->|Export / View| F

    %% Estilos
    classDef fuente fill:#f9f9f9,stroke:#333,stroke-width:1px;
    classDef ingesta fill:#e1f5fe,stroke:#0288d1,stroke-width:1.5px;
    classDef dw fill:#fff3e0,stroke:#f57c00,stroke-width:1.5px;
    classDef analitica fill:#e8f5e9,stroke:#388e3c,stroke-width:1.5px;

    class A,A1 fuente;
    class B,B1,B2,B3 ingesta;
    class C,D,D1,D2 dw;
    class E,E1,E2,E3 analitica;