"""Punto de entrada: extrae, transforma y carga."""
import logging
import time
from pyspark.sql import SparkSession

from config import load_settings
from extract import read_source
from load import write_target
from transform import transform

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("etl")


def build_spark(s) -> SparkSession:
    return (
        SparkSession.builder.appName(s.app_name)
        .master(s.spark_master)
        .config("spark.driver.memory", s.driver_memory)
        .config("spark.executor.memory", s.executor_memory)
        .config("spark.executor.cores", str(s.executor_cores))
        .config("spark.sql.shuffle.partitions", str(s.shuffle_partitions))
        .getOrCreate()
    )


def main() -> None:
    settings = load_settings()
    spark = build_spark(settings)
    try:
        df_a = read_source(spark, settings)
        if settings.cache_source:
            df_a.cache()  # df_a alimenta 3 ramas del plan

        resultado = transform(df_a)

        t0 = time.time()
        write_target(resultado, settings)
        log.info("Carga finalizada en %.1f minutos", (time.time() - t0) / 60)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
