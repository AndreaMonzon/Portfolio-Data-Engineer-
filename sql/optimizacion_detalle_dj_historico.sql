WITH base_ult_rectificativa AS (
  -- 1. Filtrar únicamente la rectificativa más reciente por cada anticipo/actividad
  SELECT 
    d.*,
    c.fecha_vencimiento,
    ROW_NUMBER() OVER (
      PARTITION BY d.cuit, d.anticipo, d.tipo_contrib, d.tratamiento, d.regimen, d.codigo_naes_unificado
      ORDER BY d.numero_rectificativa DESC
    ) AS rn_rect
  FROM analitic.VW_DETALLE_DJ_AGREGADO d
  JOIN analitic.cabecera_dj c
    ON d.anticipo = c.anticipo 
   AND d.cuit = c.cuit 
   AND d.numero_rectificativa = c.numero_rectificativa
 
),
datos_filtrados AS (
  SELECT *
  FROM base_ult_rectificativa
  WHERE rn_rect = 1
),
con_historico AS (
  -- 2. Obtener métricas del período inmediato anterior (LAG 1) y del año anterior (LAG 12)
  SELECT 
    t.*,
    
    -- Rectificativa anterior inmediata
    LAG(t.numero_rectificativa, 1) OVER (
      PARTITION BY t.cuit, t.anticipo, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.numero_rectificativa
    ) AS rect_ant_calculada,

    -- Valores del período inmediato anterior (LAG 1)
    LAG(t.base_imponible, 1) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS base_imponible_anterior,

    LAG(t.alicuota_declarada, 1) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS alicuota_declarada_anterior,

    LAG(t.impuesto, 1) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS impuesto_anterior,

    LAG(t.base_imponible_art8, 1) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS base_imponible_art8_anterior,

    LAG(t.impuesto_art8, 1) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS impuesto_art8_anterior,

    LAG(t.imp_div, 1) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS imp_div_anterior,

    -- Métricas del año anterior (LAG 12 anticipos)
    LAG(t.base_imponible, 12) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS base_imponible_anio_anterior,
    
    LAG(t.alicuota_declarada, 12) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS alicuota_declarada_anio_anterior,
    
    LAG(t.impuesto, 12) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS impuesto_anio_anterior,
    
    LAG(t.numero_rectificativa, 12) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS max_rectificativa,
    
    LAG(t.base_imponible_art8, 12) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS base_imponible_art8_anio_anterior,
    
    LAG(t.impuesto_art8, 12) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS impuesto_art8_anio_anterior,
    
    LAG(t.procesado_art8, 12) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS procesado_art8_anio_anterior,
    
    LAG(t.fecha_presentacion, 12) OVER (
      PARTITION BY t.cuit, t.tipo_contrib, t.tratamiento, t.regimen, t.codigo_naes_unificado
      ORDER BY t.anticipo
    ) AS fecha_pres_anio_anterior

  FROM datos_filtrados t
)
SELECT 
  cuit, anticipo, anticipo_fecha, anio, numero_cuota, cod_grupo, desc_grupo,
  cod_subgrupo, desc_subgrupo, actividad, tratamiento, regimen, base_imponible,
  base_imponible_anterior, base_imponible_anio_anterior,
  alicuota_declarada_anterior, alicuota_declarada, alicuota_declarada_anio_anterior,
  impuesto, impuesto_anterior, impuesto_anio_anterior,
  numero_rectificativa, 
  
  DECODE(rect_ant_calculada, -1, NULL, rect_ant_calculada) AS rect_ant,
  
  max_rectificativa, base_imponible_art8, base_imponible_art8_anterior,
  base_imponible_art8_anio_anterior, impuesto_art8, impuesto_art8_anterior,
  impuesto_art8_anio_anterior, procesado_art8, procesado_art8_anio_anterior,
  imp_div, imp_div_anterior, fecha_presentacion, fecha_pres_anio_anterior,
  codigo_naes_unificado, codigo_cuacm_unificado, codigo_naecba_unificado,
  tipo_contrib, fecha_vencimiento,
  
  CASE 
    WHEN fecha_presentacion <= TRUNC(LAST_DAY(fecha_vencimiento)) THEN 'si' 
    ELSE 'No' 
  END AS corriente_mes,
  
  CASE 
    WHEN fecha_presentacion <= TRUNC(fecha_vencimiento, 'YYYY') + INTERVAL '1' YEAR - INTERVAL '1' DAY THEN 'si' 
    ELSE 'No' 
  END AS corriente_anio,
  
  total_col
FROM con_historico;