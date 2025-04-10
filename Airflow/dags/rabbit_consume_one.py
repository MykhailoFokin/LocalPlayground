from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator
from utils.rabbitmq.source import postgres_init, consume_one, insert_xcom_to_postgres


dag_description = """
# RabbitMQ Consumer DAG - 1 minute of work

This DAG manages a RabbitMQ consumer that persists messages to PostgreSQL.

## Overview

The DAG starts a consumer that listens to the two queues `info_test_queue` 
and `data_test_queue` on RabbitMQ.
Each received message is processed and inserted into the `rabbitmq_messages`
table in the PostgreSQL database. The consumer's lifecycle is controlled 
internally and after 1 minute of consumption it will stop.

## Tasks

1.  **check_db_table_exists:** Check that target table exist at Postgres and
    create it if not.

2.  **consume_rabbitmq_one:** This task initiates the RabbitMQ consumer in a
    separate process or thread. It consumes messages for a minute and inserts
    them into PostgreSQL until the stop signal is received.

    ```python
    # Example of what the consumer might do
    def consume_one():
        # ... RabbitMQ connection and consuming logic ...
        pass
    ```

3.  **insert_to_postgres:** This task get what was consumed from xcom
    and insert it to Postgres table `rabbitmq_messages`.

    ```python
    # Example of the stop function
    def stop_consumer_function():
        # ... Database connection and update logic ...
        pass
    ```

4.  **consume_rabbitmq_one_data_queue:** The same as consume_rabbitmq_one just 
    process `data_test_queue` queue.

5.  **consume_rabbitmq_one_data_queue:** The same as insert_to_postgres just 
    process `data_test_queue` queue.

"""


with DAG(
    dag_id='rabbitmq_consume_one',
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['Basic','rabbitMQ'],
    on_failure_callback=True,
    description="This DAG a RabbitMQ consumer, it will work for a minute and stop. Consume from both queues, info and data.",
    doc_md=dag_description
) as dag:
    
    consumer_task_id = 'consume_rabbitmq_one'
    consumer_task_id_data_queue = 'consume_rabbitmq_one_data_queue'
    
    check_db_table_exists = PythonOperator(
        task_id='check_db_table_exists',
        python_callable=postgres_init,
    )
    
    consume_rabbitmq_one = PythonOperator(
        task_id=consumer_task_id,
        python_callable=consume_one,
        op_kwargs = {
            "queue_id": "info_test_queue"
        },
        provide_context=True,
    )
    
    insert_to_postgres = PythonOperator(
        task_id='insert_to_postgres',
        python_callable=insert_xcom_to_postgres,
        op_kwargs = {
            "consumer_task_id": consumer_task_id
        },
        provide_context=True,
    )
    
    consume_rabbitmq_one_data_queue = PythonOperator(
        task_id=consumer_task_id_data_queue,
        python_callable=consume_one,
        op_kwargs = {
            "queue_id": "data_test_queue"
        },
        provide_context=True,
    )
    
    insert_to_postgres_data_queue = PythonOperator(
        task_id='insert_to_postgres_data_queue',
        python_callable=insert_xcom_to_postgres,
        op_kwargs = {
            "consumer_task_id": consumer_task_id_data_queue
        },
        provide_context=True,
    )

    check_db_table_exists >> consume_rabbitmq_one >> insert_to_postgres
    check_db_table_exists >> consume_rabbitmq_one_data_queue >> insert_to_postgres_data_queue