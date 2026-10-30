"""Orquestador del pipeline ETL SIRCAR / SIFERE / SIRCREB."""
import glob
import logging
import os
import shutil
import zipfile
from pathlib import Path
from typing import List, Optional

from .config import RESULT_DIR, TABLES
from .db import crear_connection
from .loaders import load_sircar, load_sifere, load_sircreb

log = logging.getLogger(__name__)


def _txt_intermedios(work_dir: Path) -> List[str]:
    return [
        str(p) for p in work_dir.glob("*.txt") if "RecaudDetalle" not in p.name
    ]


def unzip_por_regimen(patron: str, work_dir: Path) -> List[str]:
    zips = glob.glob(str(work_dir / patron))
    for z in zips:
        with zipfile.ZipFile(z) as ref:
            ref.extractall(work_dir)
    return zips


def limpiar_txt(work_dir: Path) -> None:
    for f in _txt_intermedios(work_dir):
        try:
            os.remove(f)
        except OSError as e:
            log.warning("No se pudo borrar %s: %s", f, e)


def _concatenar(destino: Path, archivos: List[str]) -> None:
    with open(destino, "w", encoding="utf-8") as out:
        for a in archivos:
            ap = Path(a)
            if ap.exists():
                out.write(ap.read_text(encoding="utf-8"))


def procesar_sircar(work_dir: Path) -> None:
    zips = unzip_por_regimen("*_sircar_*.zip", work_dir)
    if not zips:
        log.info("[SIRCAR] sin archivos")
        return

    areas = [os.path.basename(z)[0:3] for z in zips]

    encabezado = work_dir / "SIRCAR_ENCABEZADO_ACREDITACIONES.txt"
    encabezado.write_text(
        "COD_AREA;CUIT;RAZON_SOCIAL;NRO_INGRESO_BRUTO;ANIO_RECA;"
        "MES_RECA;NRO_BOLETA;FECHA_PAGO;TIPO_PAGO;SIGNO_IMPORTE;"
        "IMPORTE;FECHA_ACRED;TIPO_ADHESION;TRAMO_DDJJ\n",
        encoding="utf-8",
    )

    archivos = [str(encabezado)] + [
        str(work_dir / "SIRCAR_ACREDITACIONES_CORREGIDO_{}.txt".format(a)) for a in areas
    ]

    destino = RESULT_DIR / "SIRCAR_ACREDITACIONES_CORREGIDOS_TOT.txt"
    _concatenar(destino, archivos)
    limpiar_txt(work_dir)

    conn = crear_connection()
    try:
        load_sircar(destino, TABLES["sircar"], conn)
    finally:
        conn.close()


def procesar_sifere(work_dir: Path) -> None:
    txt_files = list(work_dir.glob("*.txt"))
    if not txt_files:
        log.info("[SIFERE] sin archivos")
        return

    encabezado = work_dir / "SIFERE_ENCABEZADO_ACREDITACIONES.txt"
    encabezado.write_text(
        "CUIT;Nro_Inscripcion;Sicom;Razon_Social;Periodo;Jur;Form;"
        "Impuesto;Banco;Nro_Trans_Afip;Fecha_Acreditacion;Fecha_Pago;"
        "Credito_Bruto;Comisiones;IVA;Intereses;Credito_Neto\n",
        encoding="utf-8",
    )

    archivos = [str(encabezado)] + [
        str(work_dir / "SIFERE_ACREDITACIONES_CORREGIDO_{}.txt".format(a))
        for a in ["901", "904", "905", "906", "908"]
    ]

    destino = RESULT_DIR / "SIFERE_ACREDITACIONES_CORREGIDOS_TOT.txt"
    _concatenar(destino, archivos)
    limpiar_txt(work_dir)

    conn = crear_connection()
    try:
        load_sifere(destino, TABLES["sifere"], conn)
    finally:
        conn.close()


def procesar_sircreb(work_dir: Path) -> None:
    zips = unzip_por_regimen("*_sircreb_*.zip", work_dir)
    if not zips:
        log.info("[SIRCREB] sin archivos")
        return

    areas = [os.path.basename(z)[0:3] for z in zips]

    encabezado = work_dir / "SIRCREB_ENCABEZADO_PAGOS.txt"
    encabezado.write_text(
        "COD_AREA,CUIT,ANIO,MES,DECENA_MES,FECHA_PAGO,"
        "OBLIGACION_FISCAL,RECTIFICATIVA,IMPORTE_INTERES,"
        "SIGNO_INTERES,IMPORTE_RECAUDACIONES,SIGNO_RECA,IMPORTE_TOTAL\n",
        encoding="utf-8",
    )

    archivos = [str(encabezado)] + [
        str(work_dir / "SIRCREB_PAGOS_CORREGIDO_{}.txt".format(a)) for a in areas
    ]

    destino = RESULT_DIR / "SIRCREB_PAGOS_CORREGIDOS_TOT.txt"
    _concatenar(destino, archivos)
    limpiar_txt(work_dir)

    conn = crear_connection()
    try:
        load_sircreb(destino, TABLES["sircreb"], conn)
    finally:
        conn.close()


def ejecutar_etl_comarb(work_dir: Optional[str] = None) -> None:
    """
    Pipeline completo SIRCAR → SIFERE → SIRCREB.
    Al terminar archiva los archivos procesados en staging/procesados/.
    """
    work_dir = Path(
        work_dir
        or os.getenv("COMARB_DESTINO", "/opt/airflow/data/comarb_staging")
    )

    if not work_dir.is_dir():
        raise FileNotFoundError("work_dir no existe: {}".format(work_dir))

    log.info("ETL COMARB — work_dir = %s", work_dir)
    procesar_sircar(work_dir)
    procesar_sifere(work_dir)
    procesar_sircreb(work_dir)

    archivo_dir = work_dir / "procesados"
    archivo_dir.mkdir(exist_ok=True)
    for patron in ("*.zip", "*.txt"):
        for p in work_dir.glob(patron):
            shutil.move(str(p), archivo_dir / p.name)
    log.info("ETL COMARB finalizado — archivos archivados en %s", archivo_dir)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    ejecutar_etl_comarb()