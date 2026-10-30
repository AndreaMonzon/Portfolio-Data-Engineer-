import hashlib
import json
import logging
import os
import shutil
from datetime import datetime
from typing import Dict, List, Optional

log = logging.getLogger(__name__)

CONFIG = {
    "SIFERE":  ["901", "904", "905", "906", "908"],
    "SIRCAR":  ["904", "905", "906", "908"],
    "SIRCREB": ["901", "904", "905", "906", "908", "916"],
}


def _es_archivo_valido(nombre: str) -> bool:
    return not (nombre.startswith("~$") or nombre.startswith("."))


def _sha256(path: str, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(chunk), b""):
            h.update(bloque)
    return h.hexdigest()


def _cargar_registro(path: str) -> Dict:
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _guardar_registro(path: str, data: Dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def procesar_copiar_archivos(
    raiz: Optional[str] = None,
    destino: Optional[str] = None,
    registro: Optional[str] = None,
) -> List[str]:
    raiz     = raiz     or os.getenv("COMARB_RAIZ",     "/opt/airflow/data/comarb")
    destino  = destino  or os.getenv("COMARB_DESTINO",  "/opt/airflow/data/comarb_staging")
    registro = registro or os.getenv("COMARB_REGISTRO", "/opt/airflow/data/comarb_procesados.json")

    if not os.path.isdir(raiz):
        raise FileNotFoundError("Raíz COMARB no existe o no está montada: {}".format(raiz))

    os.makedirs(destino, exist_ok=True)
    procesados = _cargar_registro(registro)

    nuevos = []  # type: List[str]

    for sistema, subcarpetas in CONFIG.items():
        for sub in subcarpetas:
            carpeta = os.path.join(raiz, sistema, sub)
            if not os.path.isdir(carpeta):
                log.warning("Carpeta inexistente: %s", carpeta)
                continue

            archivos = [
                os.path.join(carpeta, f)
                for f in os.listdir(carpeta)
                if os.path.isfile(os.path.join(carpeta, f)) and _es_archivo_valido(f)
            ]
            if not archivos:
                log.warning("Sin archivos válidos en %s", carpeta)
                continue

            origen = max(archivos, key=os.path.getmtime)
            huella = _sha256(origen)

            if huella in procesados:
                log.info("%s/%s: ya procesado (%s), skip.", sistema, sub, huella[:10])
                continue

            destino_final = os.path.join(destino, sistema, sub, os.path.basename(origen))
            os.makedirs(os.path.dirname(destino_final), exist_ok=True)
            shutil.copy2(origen, destino_final)

            procesados[huella] = {
                "origen":    origen,
                "destino":   destino_final,
                "procesado": datetime.now().isoformat(timespec="seconds"),
            }
            nuevos.append(destino_final)
            log.info("%s/%s -> %s (nuevo)", sistema, sub, destino_final)

    _guardar_registro(registro, procesados)
    log.info("Archivos nuevos: %d. Total histórico: %d.", len(nuevos), len(procesados))
    return nuevos