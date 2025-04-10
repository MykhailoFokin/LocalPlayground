from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator
from utils.rabbitmq.source import postgres_init, rabbitmq_modify_consumer_status


dag_description = """
# RabbitMQ Stop Controlled Consumer DAG

This DAG manages a RabbitMQ consumer **rabbit_consumer_job_start** DAG that persists messages to PostgreSQL.

## Overview

The DAG send stop message to a consumer that listens to the `info_test_queue` on RabbitMQ.
So basically updates the flag to notify consumer to stop after next message 
will be processed. The consumer's lifecycle is controlled by
a database flag in the `consumer_control` table.

## Tasks

1.  **check_db_table_exists:** Check that target table exist at Postgres and
    create it if not.

2.  **stop_rabbitmq_consumer:** This task updates the `is_running` flag in the
    `consumer_control` table to `FALSE`, signaling the consumer to stop.

    ```python
    # Example of the stop function
    def stop_consumer_function():
        # ... Database connection and update logic ...
        pass
    ```

## Control Mechanism

The DAG uses a `consumer_control` table in PostgreSQL with an `is_running`
column (BOOLEAN). The `start_rabbitmq_consumer` task periodically checks
this flag. The `stop_rabbitmq_consumer` task sets this flag to `FALSE`.
"""


with DAG(
    dag_id='rabbitmq_consumer_job_stop',
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['Basic','rabbitMQ'],
    on_failure_callback=True,
    description="This DAG controls a RabbitMQ consumer (depends on rabbitmq_consumer_job_start only), stopping it based on a database flag. It will consume messages and then check stop status.",
    doc_md=dag_description
) as dag:
    
    # Just to not fail next one
    check_db_table_exists = PythonOperator(
        task_id='check_db_table_exists',
        python_callable=postgres_init,
    )

    send_stop_consumer_rabbitmq = PythonOperator(
        task_id='send_stop_consumer_rabbitmq',
        python_callable=rabbitmq_modify_consumer_status, 
        op_kwargs = {
            "status": False
        },
        provide_context=True,
    )

    check_db_table_exists >> send_stop_consumer_rabbitmq