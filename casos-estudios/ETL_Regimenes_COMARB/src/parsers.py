from datetime import datetime
import csv

# ---------- Helpers ----------
def _to_int(v):
    v = (v or "").strip()
    return int(v) if v else None


def _to_date(v, fmt):
    v = (v or "").strip()
    try:
        return datetime.strptime(v, fmt) if v else None
    except ValueError:
        return None


# ---------- SIRCAR (ancho fijo) ----------
SIRCAR_OFFSETS = [
    (0, 11), (11, 81), (81, 91), (91, 95), (95, 97),
    (97, 109), (109, 117), (117, 120), (120, 121),
    (121, 139), (139, 147), (147, 148), (148, None),
]
SIRCAR_NUM_COLS = {0, 1, 4, 5, 8, 9, 13}
SIRCAR_DATE_COLS = {7: "%Y%m%d", 11: "%Y%m%d"}


def parse_sircar_line(line: str, cod_area: str) -> list:
    campos = [line[a:b] for a, b in SIRCAR_OFFSETS]
    out = []
    for i, v in enumerate(campos):
        if i in SIRCAR_DATE_COLS:
            out.append(_to_date(v, SIRCAR_DATE_COLS[i]))
        elif i in SIRCAR_NUM_COLS:
            out.append(_to_int(v))
        else:
            out.append(v.strip())
    # COD_AREA siempre primero
    return [int(cod_area)] + out[1:]


# ---------- SIRCREB (ancho fijo) ----------
SIRCREB_OFFSETS = [
    (0, 11), (11, 15), (15, 17), (17, 18), (18, 26),
    (26, 64), (64, 66), (66, 84), (84, 85), (85, 103),
    (103, 104), (104, None),
]


def parse_sircreb_line(line: str, cod_area: str) -> list:
    campos = [line[a:b].strip() for a, b in SIRCREB_OFFSETS]
    return [
        int(cod_area),
        _to_int(campos[0]),                 # CUIT_AGENTE
        _to_int(campos[1]),                 # ANIO
        _to_int(campos[2]),                 # MES
        _to_int(campos[3]),                 # DECENA_MES
        _to_date(campos[4], "%Y%m%d"),      # FECHA_PAGO
        campos[5],                          # OBLIGACION_FISCAL
        _to_int(campos[6]),                 # RECTIFICATIVA
        _to_int(campos[7]),                 # IMPORTE_INTERES
        _to_int(campos[8]),                 # SIGNO_INTERES
        _to_int(campos[9]),                 # IMPORTE_RECAUDACIONES
        _to_int(campos[10]),                # SIGNO_RECA
        _to_int(campos[11]),                # IMPORTE_TOTAL
    ]


# ---------- SIFERE (csv delimitado) ----------
def iter_sifere(ruta):
    with open(ruta, encoding="latin-1") as f:
        lector = csv.reader(f, delimiter=";", quotechar='"')
        for _ in range(2):
            next(lector, None)      # salta 2 líneas de encabezado
        for fila in lector:
            if len(fila) < 17:
                continue
            fila[4] = fila[4].split()[0] if fila[4].strip() else None
            for i in range(12, 17):
                fila[i] = fila[i].replace(".", "").replace(",", ".") if fila[i].strip() else None
            yield fila