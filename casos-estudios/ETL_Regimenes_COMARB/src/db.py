import oracledb
from .config import DB


def crear_connection():
    try:
        oracledb.init_oracle_client(lib_dir=DB["lib_dir"])
        return oracledb.connect(
            user=DB["user"], password=DB["password"], dsn=DB["dsn"]
        )
    except Exception as e:
        print(f"Error de conexion a Oracle: {e}")
        return None