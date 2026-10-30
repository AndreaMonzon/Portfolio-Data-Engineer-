from datetime import datetime, timedelta
import glob
import os

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.exceptions import AirflowSkipException

BASE_DIR = os.getenv("COMARB_RAIZ", "/opt/airflow/data/comarb")
REQUIRED_FOLDERS =  ["901", "904", "905", "906", "908", "916"]


def gatekeeper_check_files():
    missing = []
    for folder in REQUIRED_FOLDERS:
        target = os.path.join(BASE_DIR, folder)
        files = glob.glob(os.path.join(target, "*")) if os.path.exists(target) else []
        if not files:
            missing.append(folder)

    if missing:
        raise AirflowSkipException(
            f"Gatekeeper: Faltan archivos en {missing}. Se saltea la ejecución."
        )
    print(f"Gatekeeper OK: archivos presentes en {REQUIRED_FOLDERS}.")


def task_cp_archivos(**context):
    from src.cp_archivos import procesar_copiar_archivos
    nuevos = procesar_copiar_archivos()
    context["ti"].xcom_push(key="archivos_nuevos", value=nuevos)
    return nuevos


def task_main_etl(**context):
    nuevos = context["ti"].xcom_pull(key="archivos_nuevos") or []
    if not nuevos:
        raise AirflowSkipException("Sin archivos nuevos, no se corre el ETL.")
    from src.main import ejecutar_etl_comarb
    
    ejecutar_etl_comarb()


default_args = {
    "owner": "data_engineer",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="comarb_etl_pipeline",
    default_args=default_args,
    description="Pipeline ETL automatizado de COMARB con Airflow y Oracle",
    schedule="0 8 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=["COMARB", "ETL", "Oracle", "Production"],
) as dag:

    check_files = PythonOperator(
        task_id="gatekeeper_check_files",
        python_callable=gatekeeper_check_files,
    )

    cp_archivos = PythonOperator(
        task_id="prepare_and_copy_files",
        python_callable=task_cp_archivos,
    )

    load_oracle = PythonOperator(
        task_id="load_etl_to_oracle",
        python_callable=task_main_etl,
        retries=0,
    )

    check_files >> cp_archivos >> load_oracle