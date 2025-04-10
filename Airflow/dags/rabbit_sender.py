from airflow import DAG
from datetime import datetime
from airflow.operators.python import PythonOperator
import logging
import time
from utils.rabbitmq.source import send_message as rabbitmq_send_message
import uuid


dag_description = """
# RabbitMQ Message Sender DAG

This DAG is responsible for pushing a predefined number of messages to a RabbitMQ exchange.

## Overview

The DAG consists of a single task that iterates through a specified number and a list of routing keys to send messages to the 'topic_logs_exchange' on the configured RabbitMQ instance.

## Tasks

1.  **my_python_task:** This task executes the `push_messages` Python function.

    ### `push_messages(message_number)`

    This function performs the following actions:

    -   Logs the start of the message pushing process.
    -   Iterates from 1 up to (but not including) the `message_number` provided in the `op_kwargs`.
    -   For each number, it iterates through a list of routing keys: `['message.info', 'message.data']`.
    -   Based on the routing key:
        -   If the key contains 'info', it constructs a message with the format:
            `'Message_' + str(num) + '_' + str(uuid.uuid4().hex)`
        -   Otherwise (if the key is 'message.data'), it constructs a message with the format:
            `'Important_data_' + str(num) + '_' + str(uuid.uuid4().hex)`
        -   It then calls the `rabbitmq_send_message` function to publish the generated message to the 'topic_logs_exchange' with the current routing key.
        -   Logs the successful push of each message, including the key and value.
    -   Finally, logs the completion of the message pushing process.

The number of messages pushed can be controlled by the `message_number` parameter in the `op_kwargs` of the `my_python_task`. To send more messages, you can either modify this parameter in the DAG definition or trigger the DAG again.
"""

def push_messages(message_number):
    logging.info("Start pushing messages.")
    routing_keys = ['message.info', 'message.data']

    for num in range(1,message_number,1):
        for key in routing_keys:
            if 'info' in key:
                message_value = 'Message_' + str(num) + '_' + str(uuid.uuid4().hex)
            else:
                message_value = 'Important_data_' + str(num) + '_' + str(uuid.uuid4().hex)
            rabbitmq_send_message(key, message_value)
            logging.info(f"Pushed: (Key:{key}, Value:{message_value})")
    logging.info("All messages pushed.")


with DAG(
    dag_id='rabbitmq_sender',
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=['Basic','rabbitMQ'],
    on_failure_callback=True,
    description="This DAG a RabbitMQ sender, it will push a few message to a queue and stop. In order to push more, just increase it at the code or run again to push the same amount of messages.",
    doc_md=dag_description,
) as dag:
    
    send_messages_rabbitmq = PythonOperator(
        task_id='my_python_task',
        python_callable=push_messages,
        op_kwargs={"message_number": 10}
    )