import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
RESULT_DIR = BASE_DIR / "Resultado"
RESULT_DIR.mkdir(exist_ok=True)

DB = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "dsn": os.getenv("DB_DSN"),
    "lib_dir": os.getenv("DB_LIB_DIR"),
}

# Prefijos de área por régimen
AREAS = {
    "sircar": ["901", "904", "905", "906", "908"],
    "sircreb": ["901", "904", "905", "906", "908", "916"],
    "sifere": ["901", "904", "905", "906", "908"],
}

# Mapping de columnas por régimen (para los INSERT)
TABLES = {
    "sircar": "ACREDITACIONES_SIRCAR",
    "sifere": "ACREDITACIONES_SIFERE",
    "sircreb": "pagos_sircreb",
}