"""Lectura desde Oracle por JDBC."""
import logging
from pyspark.sql import DataFrame, SparkSession
from config import Settings

log = logging.getLogger(__name__)


def build_source_query(table: str, anio_desde: int, anio_hasta: int) -> str:
    # int() evita que entre texto arbitrario en el SQL.
    desde, hasta = int(anio_desde), int(anio_hasta)
    return f"""(
    SELECT * FROM {table}
    WHERE ANIO BETWEEN {desde} AND {hasta}
    AND NOT (
        (CONCEPTO_CTA_CTE = 9998 OR CONCEPTO_CTA_CTE = 9999)
        AND (SUBCONCEPTO_CTA_CTE = 9998 OR SUBCONCEPTO_CTA_CTE = 9999)
    )
) tmp"""


def read_source(spark: SparkSession, s: Settings) -> DataFrame:
    reader = (
        spark.read.format("jdbc")
        .option("url", s.jdbc_url)
        .option("dbtable", build_source_query(s.source_table, s.anio_desde, s.anio_hasta))
        .option("user", s.db_user)
        .option("password", s.db_password)
        .option("driver", s.db_driver)
        .option("fetchsize", str(s.fetch_size))
    )

    years = s.anio_hasta - s.anio_desde + 1
    if years > 1:
        # Se reparte la lectura por año: más particiones que años no aportan.
        n = min(s.read_partitions, years)
        log.info("Lectura JDBC particionada por ANIO (%s particiones)", n)
        reader = (
            reader.option("partitionColumn", "ANIO")
            .option("lowerBound", str(s.anio_desde))
            .option("upperBound", str(s.anio_hasta))
            .option("numPartitions", str(n))
        )
    else:
        log.info("Un solo año: la lectura JDBC no se puede paralelizar por ANIO")

    return reader.load()
