"""Escritura del resultado en Oracle."""
import logging
from pyspark.sql import DataFrame
from config import Settings

log = logging.getLogger(__name__)


def write_target(df: DataFrame, s: Settings) -> None:
    (
        df.write.format("jdbc")
        .option("url", s.jdbc_url)
        .option("dbtable", s.target_table)
        .option("user", s.db_user)
        .option("password", s.db_password)
        .option("driver", s.db_driver)
        .option("batchsize", str(s.write_batch_size))
        .option("isolationLevel", "NONE")
        .option("truncate", "true")  # con overwrite hace TRUNCATE en vez de DROP
        .mode("overwrite")
        .save()
    )
