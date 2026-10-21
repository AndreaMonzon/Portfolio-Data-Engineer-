"""Orquestador del pipeline ETL SIRCAR / SIFERE / SIRCREB."""
import glob
import os
import shutil
import zipfile
from pathlib import Path

from .config import RESULT_DIR, TABLES
from .db import crear_connection
from .loaders import load_sircar, load_sifere, load_sircreb


def unzip_por_regimen(patron: str):
    zips = glob.glob(patron)
    for z in zips:
        with zipfile.ZipFile(z) as ref:
            ref.extractall("")
    return zips


def limpiar_txt():
    for f in glob.glob("*.txt"):
        if "RecaudDetalle" not in f:
            os.remove(f)


def _concatenar(destino: Path, archivos: list):
    with open(destino, "w") as out:
        for a in archivos:
            if os.path.exists(a):
                out.write(open(a).read())


# ---------- SIRCAR ----------
def procesar_sircar():
    zips = unzip_por_regimen("*_sircar_*.zip")
    if not zips:
        print("[SIRCAR] sin archivos"); return
    areas = [z[0:3] for z in zips]

    with open("SIRCAR_ENCABEZADO_ACREDITACIONES.txt", "w") as f:
        f.write("COD_AREA;CUIT;RAZON_SOCIAL;NRO_INGRESO_BRUTO;ANIO_RECA;"
                "MES_RECA;NRO_BOLETA;FECHA_PAGO;TIPO_PAGO;SIGNO_IMPORTE;"
                "IMPORTE;FECHA_ACRED;TIPO_ADHESION;TRAMO_DDJJ\n")
    archivos = ["SIRCAR_ENCABEZADO_ACREDITACIONES.txt"]
    for a in areas:
        archivos.append(f"SIRCAR_ACREDITACIONES_CORREGIDO_{a}.txt")

    _concatenar(RESULT_DIR / "SIRCAR_ACREDITACIONES_CORREGIDOS_TOT.txt", archivos)
    limpiar_txt()

    conn = crear_connection()
    load_sircar(RESULT_DIR / "SIRCAR_ACREDITACIONES_CORREGIDOS_TOT.txt",
                TABLES["sircar"], conn)
    conn.close()


# ---------- SIFERE ----------
def procesar_sifere():
    txt_files = glob.glob("*.txt")
    if not txt_files:
        print("[SIFERE] sin archivos"); return

    with open("SIFERE_ENCABEZADO_ACREDITACIONES.txt", "w") as f:
        f.write("CUIT;Nro_Inscripcion;Sicom;Razon_Social;Periodo;Jur;Form;"
                "Impuesto;Banco;Nro_Trans_Afip;Fecha_Acreditacion;Fecha_Pago;"
                "Credito_Bruto;Comisiones;IVA;Intereses;Credito_Neto\n")
    archivos = ["SIFERE_ENCABEZADO_ACREDITACIONES.txt"]
    for a in ["901", "904", "905", "906", "908"]:
        archivos.append(f"SIFERE_ACREDITACIONES_CORREGIDO_{a}.txt")

    _concatenar(RESULT_DIR / "SIFERE_ACREDITACIONES_CORREGIDOS_TOT.txt", archivos)
    limpiar_txt()

    conn = crear_connection()
    load_sifere(RESULT_DIR / "SIFERE_ACREDITACIONES_CORREGIDOS_TOT.txt",
                TABLES["sifere"], conn)
    conn.close()


# ---------- SIRCREB ----------
def procesar_sircreb():
    zips = unzip_por_regimen("*_sircreb_*.zip")
    if not zips:
        print("[SIRCREB] sin archivos"); return
    areas = [z[0:3] for z in zips]

    with open("SIRCREB_ENCABEZADO_PAGOS.txt", "w") as f:
        f.write("COD_AREA,CUIT,ANIO,MES,DECENA_MES,FECHA_PAGO,"
                "OBLIGACION_FISCAL,RECTIFICATIVA,IMPORTE_INTERES,"
                "SIGNO_INTERES,IMPORTE_RECAUDACIONES,SIGNO_RECA,IMPORTE_TOTAL\n")
    archivos = ["SIRCREB_ENCABEZADO_PAGOS.txt"] + [
        f"SIRCREB_PAGOS_CORREGIDO_{a}.txt" for a in areas
    ]
    _concatenar(RESULT_DIR / "SIRCREB_PAGOS_CORREGIDOS_TOT.txt", archivos)
    limpiar_txt()

    conn = crear_connection()
    load_sircreb(RESULT_DIR / "SIRCREB_PAGOS_CORREGIDOS_TOT.txt",
                 TABLES["sircreb"], conn)
    conn.close()


# ---------- Entrypoint ----------
if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent.parent)
    print("░░░░░░░░░░░░░ 0%   SIRCAR")
    procesar_sircar()
    print("████████░░░░ 40%   SIFERE")
    procesar_sifere()
    print("██████████░░ 80%   SIRCREB")
    procesar_sircreb()
    print("██████████ 100%    ✅ ETL finalizado")   