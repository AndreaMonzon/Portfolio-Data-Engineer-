"""Configuración del ETL. Todo lo sensible o específico del entorno viene
de variables de entorno (o de un archivo .env local que NO se sube a Git)."""
import os
from dataclasses import dataclass, field

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv es opcional
    pass


def _required(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"Falta la variable de entorno obligatoria: {name}")
    return value


def _int(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


@dataclass(frozen=True)
class Settings:
    # Spark
    spark_master: str
    app_name: str
    driver_memory: str
    executor_memory: str
    executor_cores: int
    shuffle_partitions: int
    # Base de datos
    jdbc_url: str
    db_user: str
    db_password: str = field(repr=False)  # nunca se imprime en logs
    db_driver: str = "oracle.jdbc.driver.OracleDriver"
    # Tablas
    source_table: str = ""
    target_table: str = ""
    # Alcance de la carga
    anio_desde: int = 2017
    anio_hasta: int = 2017
    # Rendimiento
    read_partitions: int = 10
    fetch_size: int = 20000
    write_batch_size: int = 50000
    cache_source: bool = False


def load_settings() -> Settings:
    return Settings(
        spark_master=_required("SPARK_MASTER"),
        app_name=os.environ.get("SPARK_APP_NAME", "ETL_Cta_Cte_Modif"),
        driver_memory=os.environ.get("SPARK_DRIVER_MEMORY", "10g"),
        executor_memory=os.environ.get("SPARK_EXECUTOR_MEMORY", "3g"),
        executor_cores=_int("SPARK_EXECUTOR_CORES", 6),
        shuffle_partitions=_int("SPARK_SHUFFLE_PARTITIONS", 48),
        jdbc_url=_required("DB_JDBC_URL"),
        db_user=_required("DB_USER"),
        db_password=_required("DB_PASSWORD"),
        source_table=_required("SOURCE_TABLE"),
        target_table=_required("TARGET_TABLE"),
        anio_desde=_int("ANIO_DESDE", 2017),
        anio_hasta=_int("ANIO_HASTA", 2026),
        read_partitions=_int("READ_PARTITIONS", 10),
        fetch_size=_int("JDBC_FETCH_SIZE", 20000),
        write_batch_size=_int("JDBC_WRITE_BATCH_SIZE", 50000),
        cache_source=os.environ.get("CACHE_SOURCE", "false").lower() == "true",
    )
