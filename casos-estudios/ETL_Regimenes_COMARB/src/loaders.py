from .parsers import parse_sircar_line, parse_sircreb_line, iter_sifere


SQL_SIRCAR = """
INSERT INTO {tabla} (COD_AREA, CUIT, RAZON_SOCIAL, NRO_INGRESO_BRUTO,
 ANIO_RECA, MES_RECA, NRO_BOLETA, FECHA_PAGO, TIPO_PAGO, SIGNO_IMPORTE,
 IMPORTE, FECHA_ACRED, TIPO_ADHESION, TRAMO_DDJJ)
VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14)
"""

SQL_SIRCREB = """
INSERT INTO {tabla} (COD_AREA, CUIT_AGENTE, ANIO, MES, DECENA_MES,
 FECHA_PAGO, OBLIGACION_FISCAL, RECTIFICATIVA, IMPORTE_INTERES,
 SIGNO_INTERES, IMPORTE_RECAUDACIONES, SIGNO_RECA, IMPORTE_TOTAL)
VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13)
"""

SQL_SIFERE = """
INSERT INTO {tabla} (CUIT, NRO_INSCRIPCION, SICOM, RAZON_SOCIAL, PERIODO,
 JUR, FORM, IMPUESTO, BANCO, NRO_TRANS_AFIP, FECHA_ACREDITACION,
 FECHA_PAGO, CREDITO_BRUTO, COMISIONES, IVA, INTERESES, CREDITO_NETO)
VALUES (:1,:2,:3,:4,:5,:6,:7,:8,:9,:10,:11,:12,:13,:14,:15,:16,:17)
"""


def load_sircar(ruta, tabla, conn):
    cur = conn.cursor()
    with open(ruta, encoding="latin-1") as f:
        next(f, None)
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            cod_area = line[:3]
            try:
                cur.execute(SQL_SIRCAR.format(tabla=tabla),
                            parse_sircar_line(line, cod_area))
            except Exception as e:
                print(f"[SIRCAR] error linea: {e}")
    conn.commit()
    cur.close()


def load_sircreb(ruta, tabla, conn):
    cur = conn.cursor()
    with open(ruta, encoding="latin-1") as f:
        next(f, None)
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            cod_area = line.split(",", 1)[0]
            try:
                cur.execute(SQL_SIRCREB.format(tabla=tabla),
                            parse_sircreb_line(line.split(",", 1)[1], cod_area))
            except Exception as e:
                print(f"[SIRCREB] error linea: {e}")
    conn.commit()
    cur.close()


def load_sifere(ruta, tabla, conn):
    cur = conn.cursor()
    for d in iter_sifere(ruta):
        datos = [
            _safe_int(d[0]), _safe_int(d[1]), d[2], d[3], d[4],
            _safe_int(d[5]), _safe_int(d[6]), _safe_int(d[7]),
            d[8], _safe_int(d[9]),
            _to_date(d[10], "%d/%m/%Y"), _to_date(d[11], "%d/%m/%Y"),
            _safe_float(d[12]), _safe_float(d[13]), _safe_float(d[14]),
            _safe_float(d[15]), _safe_float(d[16]),
        ]
        try:
            cur.execute(SQL_SIFERE.format(tabla=tabla), datos)
        except Exception as e:
            print(f"[SIFERE] error insert: {e}")
    conn.commit()
    cur.close()


def _safe_int(v):  return int(v) if v and str(v).strip().isdigit() else None
def _safe_float(v):
    try: return float(v) if v else None
    except ValueError: return None
def _to_date(v, fmt):
    from datetime import datetime
    try: return datetime.strptime(v.strip(), fmt) if v and v.strip() else None
    except ValueError: return None