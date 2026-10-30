import os
from pathlib import Path

# Ya no usamos load_dotenv: las vars vienen del docker-compose.
# Si querés soportar .env local, descomentá:
# from dotenv import load_dotenv
# load_dotenv("/opt/airflow/src/.env")

# RESULT_DIR: dentro del mount data/, visible desde Windows
RESULT_DIR = Path(
    os.getenv("COMARB_RESULT_DIR", "/opt/airflow/data/comarb_staging/result")
)
RESULT_DIR.mkdir(parents=True, exist_ok=True)

DB = {
    "user":     os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "dsn":      os.getenv("DB_DSN"),
    "lib_dir":  os.getenv("DB_LIB_DIR"),   # None → modo thin
}

AREAS = {
    "sircar":  ["901", "904", "905", "906", "908"],
    "sircreb": ["901", "904", "905", "906", "908", "916"],
    "sifere":  ["901", "904", "905", "906", "908"],
}

TABLES = {
    "sircar":  "ACREDITACIONES_SIRCAR_test",
    "sifere":  "ACREDITACIONES_SIFERE_test",
    "sircreb": "pagos_sircreb_test",
}