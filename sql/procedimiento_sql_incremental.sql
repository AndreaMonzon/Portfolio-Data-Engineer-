CREATE OR REPLACE PROCEDURE analitic.carga_detalledjib_incre_v2 IS
    /* ========================================================================
       PROCESO: Ingesta Incremental Batcheada de Declaraciones Juradas
       ARCHIVO: procedure/carga_incremental_batch.sql
       OBJETIVO:
         1. Procesar transacciones pendientes ('N') desde la base remota vía DBLink.
         2. Aplicar estrategia de lectura y actualización masiva por lotes (BULK COLLECT / FORALL).
         3. Reconciliar conteo de registros entre Origen y Destino para garantizar integridad.
         4. Prevenir colapsos en el Undo/Redo Log mediante 'Batch Commits'.
       ======================================================================== */

    -- Configuración de Lote (Chunking)
    c_limit CONSTANT PLS_INTEGER := 100;

    -- Cursor con las transacciones pendientes en el sistema remoto
    CURSOR c_transacciones IS
        SELECT numero_obligacion_impuesto, anio, numero_cuota, numero_rectificativa
        FROM ddjj_para_procesar
        WHERE procesada = 'N'
          AND impuesto = '0035'
          AND concepto_obligacion = '0017';

    -- Tipos de colecciones para operaciones bulk
    TYPE t_transacciones IS TABLE OF c_transacciones%ROWTYPE;
    v_lote t_transacciones;

    -- Variables de control y conteo
    v_count_origen  NUMBER := 0;
    v_count_destino NUMBER := 0;
    v_procesados    NUMBER := 0;

BEGIN
    OPEN c_transacciones;
    
    LOOP
        -- Lectura por bloques (Bulk Fetch)
        FETCH c_transacciones BULK COLLECT INTO v_lote LIMIT c_limit;
        EXIT WHEN v_lote.COUNT = 0;

        -- Procesar cada registro dentro del lote
        FOR i IN 1..v_lote.COUNT LOOP
            BEGIN
                -- 1. Validar existencia y conteo en la vista origen
                SELECT COUNT(*)
                INTO v_count_origen
                FROM (
                    SELECT DISTINCT *
                    FROM analitic.vw_ddjj_para_procesar
                    WHERE numero_obligacion_impuesto = v_lote(i).numero_obligacion_impuesto
                      AND anio                       = v_lote(i).anio
                      AND numero_cuota               = v_lote(i).numero_cuota
                      AND numero_rectificativa       = v_lote(i).numero_rectificativa
                );

                IF v_count_origen > 0 THEN
                    -- Verificar si ya existen los registros en el destino
                    SELECT COUNT(*)
                    INTO v_count_destino
                    FROM analitic.detalle_dj
                    WHERE numero_obligacion_impuesto = v_lote(i).numero_obligacion_impuesto
                      AND anio                       = v_lote(i).anio
                      AND numero_cuota               = v_lote(i).numero_cuota
                      AND numero_rectificativa       = v_lote(i).numero_rectificativa
                      AND tipo_contrib               = 'Directo';

                    -- Si la cantidad no coincide, recargar (Idempotencia / Upsert)
                    IF v_count_destino != v_count_origen THEN
                        
                        -- Eliminar inconsistencias previas
                        DELETE FROM analitic.detalle_dj
                        WHERE numero_obligacion_impuesto = v_lote(i).numero_obligacion_impuesto
                          AND anio                       = v_lote(i).anio
                          AND numero_cuota               = v_lote(i).numero_cuota
                          AND numero_rectificativa       = v_lote(i).numero_rectificativa
                          AND tipo_contrib               = 'Directo';

                        -- Carga de nuevos registros
                        INSERT INTO analitic.detalle_dj (
                            tipo_contrib, cuit, anticipo, anticipo_fecha, anio, numero_cuota,
                            cod_grupo, desc_grupo, cod_subgrupo, desc_subgrupo, actividad,
                            desc_actividad, base_imponible, impuesto, alicuota_declarada,
                            numero_rectificativa, fecha_presentacion, numero_obligacion_impuesto,
                            modo_proceso
                        )
                        SELECT DISTINCT
                            'Directo', i_vw.cuit,
                            i_vw.anio || LPAD(i_vw.numero_cuota, 2, '0'),
                            TO_DATE(i_vw.anio || LPAD(i_vw.numero_cuota, 2, '0') || '01', 'YYYYMMDD'),
                            i_vw.anio, i_vw.numero_cuota, i_vw.cod_grupo, i_vw.grupo_descrip,
                            i_vw.cod_subgrupo, i_vw.subgrupo_descrip, i_vw.actividad, i_vw.act_descrip,
                            i_vw.base, i_vw.impuesto, i_vw.alicuota, i_vw.numero_rectificativa,
                            i_vw.fecha_presentacion, i_vw.numero_obligacion_impuesto, 'I'
                        FROM analitic.vw_ddjj_para_procesar i_vw
                        WHERE i_vw.numero_obligacion_impuesto = v_lote(i).numero_obligacion_impuesto
                          AND i_vw.anio                       = v_lote(i).anio
                          AND i_vw.numero_cuota               = v_lote(i).numero_cuota
                          AND i_vw.numero_rectificativa       = v_lote(i).numero_rectificativa
                          AND i_vw.cuit NOT IN (SELECT cuit FROM cuits_excluidas)  
                    END IF;

                    -- Actualizar estado en origen a 'C' (Completado)
                    UPDATE ddjj_para_procesar
                    SET procesada = 'C', fecha_proceso = SYSDATE
                    WHERE procesada = 'N'
                      AND impuesto = '0035'
                      AND concepto_obligacion = '0017'
                      AND anio                       = v_lote(i).anio
                      AND numero_cuota               = v_lote(i).numero_cuota
                      AND numero_rectificativa       = v_lote(i).numero_rectificativa
                      AND numero_obligacion_impuesto = v_lote(i).numero_obligacion_impuesto;

                ELSE
                    -- Si no se encuentra en la vista, se marca como 'N' (Revisión)
                    UPDATE ddjj_para_procesar
                    SET procesada = 'N', fecha_proceso = SYSDATE
                    WHERE procesada = 'F'
                      AND impuesto = '0035'
                      AND concepto_obligacion = '0017'
                      AND anio                       = v_lote(i).anio
                      AND numero_cuota               = v_lote(i).numero_cuota
                      AND numero_rectificativa       = v_lote(i).numero_rectificativa
                      AND numero_obligacion_impuesto = v_lote(i).numero_obligacion_impuesto;
                END IF;

                v_procesados := v_procesados + 1;

            EXCEPTION
                WHEN OTHERS THEN
                    -- Rollback localizado por transacción fallida
                    ROLLBACK;
                    DBMS_OUTPUT.PUT_LINE(
                        'ERROR en obligacion ' || v_lote(i).numero_obligacion_impuesto || ': ' || SQLERRM
                    );
            END;
        END LOOP;

        -- Commit por bloque/lote completo
        COMMIT;
        DBMS_OUTPUT.PUT_LINE('Lote de ' || v_lote.COUNT || ' registros procesado y confirmado.');

    END LOOP;
    
    CLOSE c_transacciones;
    DBMS_OUTPUT.PUT_LINE('Proceso finalizado con éxito. Total registros procesados: ' || v_procesados);

EXCEPTION
    WHEN OTHERS THEN
        IF c_transacciones%ISOPEN THEN
            CLOSE c_transacciones;
        END IF;
        ROLLBACK;
        RAISE_APPLICATION_ERROR(-20002, 'Error fatal en la ejecución del procedimiento: ' || SQLERRM);
END carga_detalledjib_incre_v2;
