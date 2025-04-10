from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from utils.email import CustomEmailOperator
from airflow.configuration import conf
from datetime import datetime
import logging
import os
from trino.dbapi import connect
import psycopg2
from airflow.decorators import task
from typing import List, Dict

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.dummy import DummyOperator
from utils.email import CustomEmailOperator
from airflow.configuration import conf
from datetime import datetime
import logging
import os
from trino.dbapi import connect
import psycopg2
from airflow.decorators import task
from typing import List, Dict


doc_md_DAG = """
# The Example Data Integration DAG

This DAG demonstrates a data integration pipeline using [Trino](https://trino.io/docs/current/overview/concepts.html) to move data between different data stores: 
[Minio](https://min.io/docs/minio/container/index.html) (accessed via the [Hive connector](https://trino.io/docs/current/connector/hive.html)), PostgreSQL, 
and [Iceberg tables](https://iceberg.apache.org/docs/latest/) on Minio.

## Overview

The DAG performs the following steps:

1.  **Creates Schemas (if they don't exist):**
    -   Creates a Hive schema in Trino, pointing to a location in Minio.
    -   Creates an Iceberg schema in Trino.

2.  **Creates Tables (if they don't exist):**
    -   Creates a `users` table in the Hive schema, reading data in CSV format from a specified location in Minio.
    -   Creates an `ice_users` table in the Iceberg schema, using the Parquet format.
    -   Creates a `pg_users` table in the PostgreSQL schema.

3.  **Data Transfer:**
    -   **Hive to PostgreSQL:** Reads data from the `users` table in Hive and inserts it into the `pg_users` table in PostgreSQL. Data type casting from Hive's `varchar` to PostgreSQL's `int` for the `id` column is performed.
    -   **PostgreSQL to Iceberg:** Reads data from the `pg_users` table in PostgreSQL and inserts it into the `ice_users` table in Iceberg.

4.  **Reporting:**
    -   Collects information about the execution status of each task in the DAG.
    -   Sends an email notification upon successful completion of the data integration process, including a report of the task statuses.

## Tasks

The DAG consists of the following tasks:

-   **trino_create_hive_schema:** Creates the `hive_schema` in the `hive` catalog of Trino.
-   **trino_create_hive_table:** Creates the `users` table in the `hive.hive_schema`, reading CSV data from Minio.
-   **trino_create_iceberg_schema:** Creates the `iceberg_schema` in the `iceberg` catalog of Trino.
-   **trino_create_iceberg_table:** Creates the `ice_users` table in the `iceberg.iceberg_schema` using Parquet format.
-   **trino_create_postgres_table:** Creates the `pg_users` table in the `postgresql.public` schema of Trino.
-   **trino_hive_to_postgres:** Transfers data from the `hive.hive_schema.users` table to the `postgresql.public.pg_users` table using Trino.
-   **trino_postgres_to_iceberg:** Transfers data from the `postgresql.public.pg_users` table to the `iceberg.iceberg_schema.ice_users` table using Trino.
-   **collect_task_info:** A Python task that gathers information about the execution status of other tasks in the DAG. This information is used for the success email report.
-   **templated_email_success:** A custom email operator that sends a success notification email containing a report of the task execution statuses. The email content is generated from a Jinja template (`dag_report_email.html`).

## Data Flow

The data flows through the following stages:

1.  Data originates as CSV files in Minio, accessible via the Trino Hive connector.
2.  Trino reads this data and creates the `hive.hive_schema.users` table.
3.  Trino then reads data from `hive.hive_schema.users` and writes it to the `postgresql.public.pg_users` table.
4.  Finally, Trino reads data from `postgresql.public.pg_users` and writes it to the `iceberg.iceberg_schema.ice_users` table in Parquet format on Minio.

## Prerequisites

-   Trino instance configured with Hive, Iceberg, and PostgreSQL connectors pointing to the respective data stores (Minio and PostgreSQL).
-   Environment variables configured for Trino and PostgreSQL connection details (host, port, user, password, database).
-   A Minio bucket configured with Hive metastore and containing the `example_data` for the Hive table.
-   A Jinja template `dag_report_email.html` present in the `templates` folder within the Airflow DAGs directory for the success email.
-   Email configuration set up in Airflow for sending notifications.
"""
doc_md_DAG = """
### The Exampe data integration DAG

This DAG moves data using Trino:
1. from [Minio](https://min.io/docs/minio/container/index.html) that is using [Hive connector](https://trino.io/docs/current/connector/hive.html) at [Trino](https://trino.io/docs/current/overview/concepts.html) to Postgres
2. from Postgres to icberg table located at Minio

"""

HIVE_CATALOG = "hive"
HIVE_SCHEMA = f"{HIVE_CATALOG}.hive_schema"
HIVE_TABLE = "users"
ICEBERG_CATALOG = "iceberg"
ICEBERG_SCHEMA = f"{ICEBERG_CATALOG}.iceberg_schema"
ICEBERG_TABLE = "ice_users"
POSTGRES_CATALOG = "postgresql"
POSTGRES_SCHEMA = f'{POSTGRES_CATALOG}.public'
POSTGRES_TABLE = 'pg_users'

default_args = {
    'owner': 'airflow',
    'email': ['your_email@example.com'],  # Email to send notifications to
    'email_on_failure': True,
    'email_on_retry': False,
}

def execute_query_trino(query, catalog, schema):
    try:
        logging.info("Connecting to Trino")
        step = 'Trino'
        trino_conn = connect(
            host=os.getenv('TRINO_HOST', default='localhost'),
            port=os.getenv('TRINO_PORT'),  # Default Trino port
            user=os.getenv('TRINO_USER'),
            catalog=catalog,
            schema=schema
        )
        trino_cursor = trino_conn.cursor()
        trino_cursor.execute(query)
        trino_conn.commit()        
        logging.info("Trino executed query successfully.")
    except Exception as e:
        logging.info(f"Error at query execution for Trino: {e}")
        raise
    finally:
        if trino_conn:
            trino_conn.close()

def execute_query_postgres(query):
    try:
        logging.info("Connecting to Postgres")
        pg_conn = psycopg2.connect(
            host=os.getenv('POSTGRES_HOST'),
            port=os.getenv('POSTGRES_PORT'),
            database=os.getenv('POSTGRES_DB'),
            user=os.getenv('POSTGRES_USER'),
            password=os.getenv('POSTGRES_PASSWORD')
        )
        pg_cursor = pg_conn.cursor()
        pg_cursor.execute(query)
        pg_conn.commit()
        logging.info("Execution of query done at Postgres.")
    except Exception as e:
        if pg_conn:
            pg_conn.rollback()
        logging.info(f"Error at query execution for Postgres: {e}")
        raise
    finally:
        if pg_conn:
            pg_cursor.close()
            pg_conn.close()

@task
def collect_task_info(**context) -> List[Dict]:
    """
    Collect information about task execution at DAG.
    """
    dag = context['dag']
    task_instances = context['ti'].get_dagrun().get_task_instances()
    task_info_list: List[Dict] = []
    task_order: List[str] = []
    visited_tasks = set()
    current_task_id = context['ti'].task_id
    excluded_task_ids = [current_task_id, 'templated_email_success']

    def get_task_order_recursive(current_task):
        if current_task.task_id in visited_tasks:
            return
        visited_tasks.add(current_task.task_id)
        task_order.append(current_task.task_id)
        for downstream_task_id in current_task.downstream_task_ids:
            downstream_task = dag.get_task(downstream_task_id)
            get_task_order_recursive(downstream_task)

    # Find starting tasks (that does not have upstream)
    start_tasks = [task for task in dag.tasks if not task.upstream_task_ids]
    for start_task in start_tasks:
        get_task_order_recursive(start_task)

    # Filter itself and next one
    filtered_task_order = [task_id for task_id in task_order if task_id not in excluded_task_ids]

    for index, task_id in enumerate(filtered_task_order, start=1):
        ti = next((ti for ti in task_instances if ti.task_id == task_id), None)
        if ti:
            group_name = ""
            current = dag.get_task(task_id)
            while current.task_group:
                if group_name:
                    group_name = f"{current.task_group.group_id}.{group_name}"
                else:
                    group_name = current.task_group.group_id
                current = current.task_group

            task_info_list.append({
                "order_id": str(index), 
                "group_name": group_name, 
                "task_id": ti.task_id, 
                "operator": ti.operator, 
                "status": ti.state
            })

    return task_info_list

with DAG(
    dag_id='Hive_Postgres_Iceberg',
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['Basic','Trino','Iceberg'],
    doc_md=doc_md_DAG,
    template_searchpath = os.path.join(conf['core']['dags_folder'], "templates"),
    default_args=default_args
) as dag:
    
    trino_create_hive_schema = PythonOperator(
        task_id="trino_create_hive_schema",
        python_callable=execute_query_trino,
        op_kwargs={"query": f"CREATE SCHEMA IF NOT EXISTS {HIVE_SCHEMA} WITH (LOCATION='s3a://hive/hive_schema/')",
                   "catalog": HIVE_CATALOG,
                   "schema": HIVE_SCHEMA},
    )

    # Location depends on where you put example.csv file + schema name
    trino_create_hive_table = PythonOperator(
        task_id="trino_create_hive_table",
        python_callable=execute_query_trino,
        op_kwargs={"query": f"""CREATE TABLE IF NOT EXISTS {HIVE_SCHEMA}.{HIVE_TABLE}(
                                id varchar,
                                username varchar,
                                cityname varchar
                                )
                                WITH (
                                    format='CSV',
                                    skip_header_line_count = 1,
                                    external_location='s3a://hive/hive_schema/example_data'
                                )""",
                   "catalog": HIVE_CATALOG,
                   "schema": HIVE_SCHEMA},
    )
    
    trino_create_iceberg_schema = PythonOperator(
        task_id="trino_create_iceberg_schema",
        python_callable=execute_query_trino,
        op_kwargs={"query": f"CREATE SCHEMA IF NOT EXISTS {ICEBERG_SCHEMA}",
                   "catalog": ICEBERG_CATALOG,
                   "schema": ICEBERG_SCHEMA},
    )

    trino_create_iceberg_table = PythonOperator(
        task_id="trino_create_iceberg_table",
        python_callable=execute_query_trino,
        op_kwargs={"query": f"""CREATE TABLE IF NOT EXISTS {ICEBERG_SCHEMA}.{ICEBERG_TABLE}(
                                id bigint,
                                username varchar,
                                cityname varchar
                                )
                                WITH (
                                    format = 'PARQUET'
                                )""",
                   "catalog": ICEBERG_CATALOG,
                   "schema": ICEBERG_SCHEMA},
    )

    trino_create_postgres_table = PythonOperator(
        task_id="trino_create_postgres_table",
        python_callable=execute_query_trino,
        op_kwargs={"query": f"""CREATE TABLE IF NOT EXISTS {POSTGRES_SCHEMA}.{POSTGRES_TABLE}(
                                id int,
                                username varchar,
                                cityname varchar
                                )""",
                   "catalog": POSTGRES_CATALOG,
                   "schema": POSTGRES_SCHEMA},
    )

    trino_hive_to_postgres = PythonOperator(
        task_id="trino_hive_to_postgres",
        python_callable=execute_query_trino,
        op_kwargs={"query": f"""INSERT INTO {POSTGRES_SCHEMA}.{POSTGRES_TABLE} (id, username, cityname)
                                SELECT cast(id as int), username, cityname FROM {HIVE_SCHEMA}.{HIVE_TABLE}
                            """,
                   "catalog": POSTGRES_CATALOG,
                   "schema": POSTGRES_SCHEMA},
    )

    trino_postgres_to_iceberg = PythonOperator(
        task_id="trino_postgres_to_iceberg",
        python_callable=execute_query_trino,
        op_kwargs={"query": f"""INSERT INTO {ICEBERG_SCHEMA}.{ICEBERG_TABLE} (id, username, cityname)
                                SELECT id, username, cityname FROM {POSTGRES_SCHEMA}.{POSTGRES_TABLE}
                            """,
                   "catalog": ICEBERG_CATALOG,
                   "schema": ICEBERG_SCHEMA},
    )

    report_content=collect_task_info()

    templated_email_success = CustomEmailOperator(
        task_id = 'templated_email_success',
        to = 'test@example.com',
        subject = 'DAG finished successfully',
        html_content = 'templates/dag_report_email.html',
        params = {
            "content": {
                "paragraph": "Data checks by DAG run ID <strong>{{ run_id }}</strong>",
                "messages": report_content,
            },
            "style": {
                "main_color": "success"
            }
        }
    )

    trino_create_hive_schema >> trino_create_hive_table  >> trino_hive_to_postgres
    trino_create_iceberg_schema >> trino_create_iceberg_table >> trino_hive_to_postgres
    trino_create_postgres_table >> trino_hive_to_postgres
    trino_hive_to_postgres >> trino_postgres_to_iceberg

    trino_postgres_to_iceberg >> report_content >> templated_email_success