from datetime import datetime

from airflow import DAG
from airflow.providers.standard.operators.bash import BashOperator

PROJETO = "/opt/airflow/project"

with DAG(
    dag_id="anp_fuel_pipeline",
    description="Pipeline ANP: carga Silver + modelagem dbt",
    start_date=datetime(2026, 1, 1),
    schedule=None,  # sem agendamento por ora: disparo manual
    catchup=False,
    default_args={"retries": 1},
) as dag:

    load = BashOperator(
        task_id="load_silver",
        bash_command=f"cd {PROJETO} && python src/load.py",
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=f"cd {PROJETO}/dbt && dbt run",
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=f"cd {PROJETO}/dbt && dbt test",
    )

    load >> dbt_run >> dbt_test
