from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator
from utils.rabbitmq.source import postgres_init, start_consumer


dag_description = """
# RabbitMQ Controlled Consumer DAG

This DAG manages a RabbitMQ consumer that persists messages to PostgreSQL.

## Overview

The DAG starts a consumer that listens to the `info_test_queue` on RabbitMQ.
Each received message is processed and inserted into the `rabbitmq_messages`
table in the PostgreSQL database. The consumer's lifecycle is controlled by
a database flag in the `consumer_control` table.

## Tasks

1.  **check_db_table_exists:** Check that target table exist at Postgres and
    create it if not.

2.  **start_rabbitmq_consumer:** This task initiates the RabbitMQ consumer in a
    separate process or thread. It continuously consumes messages and inserts
    them into PostgreSQL until the stop signal is received.

    ```python
    # Example of what the consumer might do
    def consume_messages():
        # ... RabbitMQ connection and consuming logic ...
        # ... Periodic check of the 'is_running' flag ...
        pass
    ```

3.  **stop_rabbitmq_consumer:** This task updates the `is_running` flag in the
    `consumer_control` table to `FALSE`, signaling the consumer to stop.

    ```python
    # Example of the stop function
    def stop_consumer_function():
        # ... Database connection and update logic ...
        pass
    ```

4.  **end:** A simple end task.

## Control Mechanism

The DAG uses a `consumer_control` table in PostgreSQL with an `is_running`
column (BOOLEAN). The `start_rabbitmq_consumer` task periodically checks
this flag. The `stop_rabbitmq_consumer` task sets this flag to `FALSE`.
"""


with DAG(
    dag_id='rabbitmq_consumer_job_start',
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['Basic','rabbitMQ'],
    on_failure_callback=True,
    description="This DAG controls a RabbitMQ consumer, starting it based on a database flag. Note: it is separate from rabbit_consume_one.",
    doc_md=dag_description
) as dag:
    
    check_db_table_exists = PythonOperator(
        task_id='check_db_table_exists',
        python_callable=postgres_init,
    )

    start_consumer_rabbitmq = PythonOperator(
        task_id='start_consumer_rabbitmq',
        python_callable=start_consumer, 
        provide_context=True,
    )

    check_db_table_exists >> start_consumer_rabbitmq