import logging
import os

import oracledb

from .config import DB

log = logging.getLogger(__name__)


def crear_connection():
    """
    Conexión Oracle. Modo thin por default (no necesita Instant Client).
    Si DB_LIB_DIR está seteado y existe, activa thick.
    """
    dsn      = DB.get("dsn")
    user     = DB.get("user")
    password = DB.get("password")
    lib_dir  = DB.get("lib_dir")

    if not all([dsn, user, password]):
        raise RuntimeError(
            "Config Oracle incompleta. Faltan DB_USER/DB_PASS/DB_DSN "
            "(user={!r}, dsn={!r}, pass_set={})".format(
                user, dsn, bool(password)
            )
        )

    # Thick mode opcional
    if lib_dir:
        if not os.path.isdir(lib_dir):
            log.warning("DB_LIB_DIR=%s no existe; usando modo thin.", lib_dir)
        else:
            try:
                oracledb.init_oracle_client(lib_dir=lib_dir)
                log.info("Oracle client inicializado (thick): %s", lib_dir)
            except Exception as e:
                # Ya inicializado en este proceso → OK
                log.info("init_oracle_client omitido (%s)", e)

    try:
        conn = oracledb.connect(user=user, password=password, dsn=dsn)
        log.info("Oracle conectado: %s (user=%s)", dsn, user)
        return conn
    except Exception as e:
        raise RuntimeError(
            "Error de conexión a Oracle ({}): {}".format(dsn, e)
        )