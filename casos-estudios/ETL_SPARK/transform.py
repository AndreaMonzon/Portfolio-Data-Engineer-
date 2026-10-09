"""Transformaciones de negocio sobre el detalle de cuentas corrientes."""
from pyspark.sql import Column, DataFrame
from pyspark.sql import functions as F

KEYS = ["CUIT", "ANIO", "NUMERO_CUOTA"]


def _ultima_fecha(df: DataFrame, subconcepto: str, alias: str) -> DataFrame:
    """Última fecha de movimiento por CUIT/año/cuota para un subconcepto."""
    return (
        df.filter(
            (F.col("CONCEPTO_OBLIGACION") == "0017")
            & (F.col("SUBCONCEPTO_CTA_CTE") == subconcepto)
        )
        .groupBy(*KEYS)
        .agg(F.max("FECHA_MOVIMIENTO").alias(alias))
    )


def _es_corriente(fecha: str) -> Column:
    """True si el movimiento ocurrió dentro del período de vencimiento.

    Concepto '0010' (anual) compara por año; el resto compara año+mes.
    """
    venc = "FECHA_VENCIMIENTO"
    anual = (F.col("CONCEPTO_OBLIGACION") == "0010") & (F.year(fecha) <= F.year(venc))
    mensual = (F.col("CONCEPTO_OBLIGACION") != "0010") & (
        (F.year(fecha) * 100 + F.month(fecha)) <= (F.year(venc) * 100 + F.month(venc))
    )
    return anual | mensual


def transform(df_a: DataFrame) -> DataFrame:
    df_b = _ultima_fecha(df_a, "0017", "Fecha_ult_mens")
    df_d = _ultima_fecha(df_a, "0117", "Max_fecha_anual")

    df_final = (
        df_a.alias("a")
        .join(df_b.alias("b"), on=KEYS, how="left")
        .join(df_d.alias("d"), on=KEYS, how="left")
    )

    fecha_movimiento = (
        F.when(
            (F.col("a.SUBCONCEPTO_CTA_CTE") == "0008")
            & (F.col("a.FECHA_MOVIMIENTO") == F.col("d.Max_fecha_anual")),
            F.col("b.Fecha_ult_mens"),
        )
        .when(
            (F.col("a.SUBCONCEPTO_CTA_CTE") == "0117")
            & (F.col("a.FECHA_MOVIMIENTO") > F.col("b.Fecha_ult_mens")),
            F.col("b.Fecha_ult_mens"),
        )
        .otherwise(F.col("a.FECHA_MOVIMIENTO"))
    )

    return df_final.select(
        "a.ANIO",
        "CONCEPTO_CTA_CTE",
        "CONCEPTO_DESCR",
        "CONCEPTO_OBLIGACION",
        F.round(F.abs(F.col("CREDITOS")), 2).alias("CREDITOS"),
        "CTO_CTA_DESCR",
        F.col("a.CUIT").cast("long").alias("CUIT"),
        F.round(F.col("DEBITOS"), 2).alias("DEBITOS"),
        fecha_movimiento.alias("FECHA_MOVIMIENTO"),
        "FECHA_MOVIMIENTO_PAGO",
        "FECHA_PRESENTACION",
        "FECHA_VENCIMIENTO",
        "IMP_DESCR",
        "IMPUESTO",
        F.col("NUMERO_ASIENTO").cast("long").alias("NUMERO_ASIENTO"),
        "a.NUMERO_CUOTA",
        "PERIODO",
        "RAZON_SOCIAL",
        "a.SUBCONCEPTO_CTA_CTE",
        "SUBCONCEPTO_DESCR",
        "VENCIMIENTO",
        F.round(
            F.when(_es_corriente("a.FECHA_MOVIMIENTO"), F.col("DEBITOS")).otherwise(0), 2
        ).alias("DEBITOS_CORRIENTE"),
        F.round(
            F.when(_es_corriente("FECHA_MOVIMIENTO_PAGO"), F.abs(F.col("CREDITOS"))).otherwise(0), 2
        ).alias("CREDITOS_CORRIENTE"),
        F.when(_es_corriente("a.FECHA_MOVIMIENTO"), "CTE").otherwise("NO_CTE").alias("TIPO_MOVIMIENTO"),
        F.col("CLAVE_IMPONIBLE").cast("long").alias("clave_imponible"),
        F.col("CTA_CTE_ID").cast("long").alias("CTA_CTE_ID"),
        F.col("NUMERO_OBLIGACION_IMPUESTO").cast("long").alias("NUMERO_OBLIGACION_IMPUESTO"),
    )
