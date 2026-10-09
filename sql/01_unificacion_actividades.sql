Documentación Funcional y Técnica

 Objetivo del Proceso
1-Unificar Nomencladores Impositivos: Homogeneizar los códigos de actividades económicas expresados en distintos esquemas impositivos 
(NAES, CUACM, NAECBA) a un estándar unificado (NAES_UNIFICADO).

2-Prorratear Valores Impositivos: Calcular el valor unitario prorrateado de la base imponible e
 impuesto (imp_div, base_imponible_div) dividiendo las métricas sobre el recuento de registros originales (total_col),
  asegurando que no existan distorsiones producidas por duplicaciones en la tabla de mapeo.

3-Mapeo Cascada (Fallback Strategy): Aplicar dos niveles de LEFT JOIN
 con la tabla de homologación (codigos_cuac_naes) 
 para resolver coincidencias directas o secundarias cuando un código carece de equivalencia primaria.



 /*------------------------------------------------------------------
   PROCESO: Estandarización de Actividades Económicas y  distribución proporcional Impositivo
   ARCHIVO: sql/01_unificacion_actividades.sql
   OBJETIVO:
     1. Homogeneizar códigos y descripciones heterogéneos (CUACM, NAECBA, NAES).
     2. Mapear equivalencias mediante estrategia de coincidencia en cascada (Fallback).
     3. Calcular métricas  distribución proporcional (imp_div, base_imponible_div) utilizando
        funciones de ventana en lugar de agregaciones agrupadas costosas.
   ------------------------------------------------------------------ */

WITH detalle_con_conteo AS (
    SELECT 
        a.TIPO_CONTRIB, 
        a.CUIT, 
        a.ANTICIPO, 
        a.ANTICIPO_FECHA, 
        a.ANIO, 
        a.NUMERO_CUOTA, 
        a.COD_GRUPO, 
        a.DESC_GRUPO, 
        a.COD_SUBGRUPO, 
        a.DESC_SUBGRUPO, 
        a.ACTIVIDAD, 
        a.DESC_ACTIVIDAD, 
        a.TRATAMIENTO, 
        a.REGIMEN, 
        a.BASE_IMPONIBLE, 
        a.ALICUOTA_DECLARADA, 
        a.IMPUESTO, 
        a.NUMERO_RECTIFICATIVA, 
        a.BASE_IMPONIBLE_ART8, 
        a.IMPUESTO_ART8, 
        a.PROCESADO_ART8, 
        a.FECHA_PRESENTACION,
        
        -- Conteo de registros base en una sola pasada (Window Function)
        COUNT(*) OVER (
            PARTITION BY a.CUIT, a.ANTICIPO, a.TIPO_CONTRIB, a.ACTIVIDAD, a.NUMERO_RECTIFICATIVA
        ) AS total_col
    FROM analitic.detalle_dj_prueba a
),
detalle_mapeado AS (
    SELECT 
        d.*,
        
        -- PRIMERA COINCIDENCIA (Mapeo directo por CUACM)
        b1.codigo_cuacm,
        b1.codigo_naes,
        b1.naecba,
        b1.descripcion_cuacm,
        b1.descripcion_naes,
        b1.descripcion_naecba,

        -- SEGUNDA COINCIDENCIA (Fallback por NAECBA si la primera no existe)
        b2.codigo_naes       AS codigo_naes2,
        b2.codigo_cuacm      AS codigo_cuacm2,
        b2.naecba            AS naecba2,
        b2.descripcion_naes  AS descripcion_naes2,
        b2.descripcion_cuacm AS descripcion_cuacm2,
        b2.descripcion_naecba AS descripcion_naecba2
    FROM detalle_con_conteo d
    LEFT JOIN analitic.codigos_cuac_naes b1 
        ON b1.cuacm_corregido = d.ACTIVIDAD
    LEFT JOIN analitic.codigos_cuac_naes b2 
        ON b2.naecba = d.ACTIVIDAD 
       AND b1.codigo_cuacm IS NULL
)
SELECT 
    TIPO_CONTRIB, 
    CUIT, 
    ANTICIPO, 
    ANTICIPO_FECHA, 
    ANIO, 
    NUMERO_CUOTA, 
    COD_GRUPO, 
    DESC_GRUPO, 
    COD_SUBGRUPO, 
    DESC_SUBGRUPO, 
    ACTIVIDAD, 
    DESC_ACTIVIDAD, 
    TRATAMIENTO, 
    REGIMEN, 
    BASE_IMPONIBLE, 
    ALICUOTA_DECLARADA, 
    IMPUESTO, 
    NUMERO_RECTIFICATIVA, 
    BASE_IMPONIBLE_ART8, 
    IMPUESTO_ART8, 
    PROCESADO_ART8, 
    FECHA_PRESENTACION, 

    codigo_cuacm, 
    codigo_cuacm2, 
    codigo_naes, 
    codigo_naes2, 
    naecba, 
    naecba2, 

    /* ------------------------------------------------------------------
       1. UNIFICACIÓN DE CÓDIGOS Y DESCRIPCIONES (HOMOGENEIZACIÓN DE CATÁLOGOS)
       ------------------------------------------------------------------ */
    DECODE(
        ACTIVIDAD,
        codigo_cuacm,  codigo_naes,
        codigo_cuacm2, codigo_naes2,
        naecba,        codigo_naes,
        naecba2,       codigo_naes2,
        ACTIVIDAD
    ) AS codigo_naes_unificado,

    DECODE(
        DESC_ACTIVIDAD,
        descripcion_cuacm,   descripcion_naes,
        descripcion_cuacm2,  descripcion_naes2,
        descripcion_naecba,  descripcion_naes,
        descripcion_naecba2, descripcion_naes2,
        DESC_ACTIVIDAD
    ) AS desc_naes_unificado,

    DECODE(
        ACTIVIDAD,
        codigo_cuacm, codigo_cuacm,
        naecba2,      codigo_cuacm2
    ) AS codigo_cuacm_unificado,

    DECODE(
        ACTIVIDAD,
        naecba2,      naecba2,
        codigo_cuacm, naecba
    ) AS codigo_naecba_unificado,

    /* ------------------------------------------------------------------
       2. MÉTRICAS de distribución proporcional Y CONTROL DE ERRORES DE DIVISIÓN POR CERO
       ------------------------------------------------------------------ */
    total_col,

    IMPUESTO / NULLIF(total_col, 0)       AS imp_div,
    BASE_IMPONIBLE / NULLIF(total_col, 0) AS base_imponible_div

FROM detalle_mapeado;