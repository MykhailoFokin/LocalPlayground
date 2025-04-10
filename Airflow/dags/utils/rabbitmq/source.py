import pika
import logging
import psycopg2
from psycopg2 import extras
import os
from threading import Thread, Event
import time


# Get Trino db connection
def get_db_connection():
    try:
        # Establish connection
        conn = psycopg2.connect(
            host     = os.getenv('POSTGRES_HOST'),
            port     = os.getenv('POSTGRES_PORT'),
            database = os.getenv('POSTGRES_TRINO_DATABASE'),
            user     = os.getenv('POSTGRES_TRINO_USER'),
            password = os.getenv('POSTGRES_TRINO_PASSWORD')
        )
        cursor = conn.cursor()

        return conn, cursor
    except psycopg2.Error as e:
        logging.info(f"PostgreSQL error: {e}")
        raise
    #finally:
    #    if conn:
    #        cursor.close()
    #        conn.close()

# Function init to create table at postgres if not exists
def postgres_init():
    try:
        # Establish connection
        conn, cursor = get_db_connection()

        POSTGRES_TABLE = os.getenv('POSTGRES_RABBITMQ_TABLE')
        logging.info(f'Check that table {POSTGRES_TABLE} exist.')

        cursor.execute(f"create table if not exists {POSTGRES_TABLE} (message_data varchar(255), dag_id varchar(255))")
        conn.commit()
        cursor.execute(f"create table if not exists rabbitmq_consumer_control (is_running BOOLEAN)")
        cursor.execute(f"insert into rabbitmq_consumer_control (is_running) select '0' where not exists (select 1 from rabbitmq_consumer_control where is_running is not null)")
        conn.commit()
    except psycopg2.Error as e:
        logging.info(f"PostgreSQL error: {e}")
        conn.rollback()
    finally:
        if conn:
            cursor.close()
            conn.close()

# Send a message
def send_message(routing_key, data):
    try:
        credentials =  pika.PlainCredentials('admin', os.getenv('RABBITMQ_PASSWORD'))
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq',credentials=credentials))
        channel = connection.channel()

        # declare a queue - in something is wrong at rabbitmq configuration
        #channel.queue_declare(queue='info_test_queue', durable=True)

        #channel.exchange_declare(exchange='topic_logs_exchange', exchange_type='topic')
        
        channel.basic_publish(exchange='topic_logs_exchange',
                            routing_key=routing_key,
                            body=data,
                            properties=pika.BasicProperties(delivery_mode=pika.DeliveryMode.Persistent)
                            )
        logging.info("Message sent.")
    except pika.exceptions.AMQPConnectionError as e:
        logging.info(f"Error connecting to RabbitMQ: {e}")
    except Exception as e:
        logging.info(f"An unexpected error occurred: {e}")
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()

def rabbitmq_modify_consumer_status(**kwargs):
    try:
        status = kwargs['status']
        # Establish connection
        conn, cursor = get_db_connection()
        cursor.execute(f"UPDATE rabbitmq_consumer_control SET is_running = {status}")
        conn.commit()
        conn.close()
        status_name = 'Start' if status == 1 else 'Stop'
        logging.info(f"Consumer sent status change to: {status_name}")
    except psycopg2.Error as e:
        logging.info(f"Error updating consumer control: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# This consumer function will work indefinitely
def start_consumer(**kwargs):
    rabbitmq_queue = 'info_test_queue'
    try:
        # Get some values
        ti = kwargs['task_instance']
        dag_id = ti.dag_id
        POSTGRES_TABLE = os.getenv('POSTGRES_RABBITMQ_TABLE')
        stop_consuming = False
        
        credentials =  pika.PlainCredentials('admin', os.getenv('RABBITMQ_PASSWORD'))
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq',credentials=credentials))
        channel = connection.channel()
        
        def callback(ch, method, properties, body):
            nonlocal stop_consuming
            try:
                message_data = body.decode()
                logging.info(f" [x] {method.routing_key}:{message_data}")

                # Establish connection
                conn, cursor = get_db_connection()
                
                # Construct and execute the INSERT statement
                sql = f"""
                    INSERT INTO {POSTGRES_TABLE} (message_data, dag_id)
                    VALUES (%s, %s);
                """

                # Extract values from message_data based on your message structure
                values = (message_data, dag_id)
                cursor.execute(sql, values)
                conn.commit()

                logging.info(f"Inserted message: {message_data}")

                ch.basic_ack(delivery_tag=method.delivery_tag) # Acknowledge message

            except psycopg2.Error as e:
                logging.info(f"PostgreSQL error: {e}")
                conn.rollback()
                # Consider requeueing the message or moving it to a dead-letter queue
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            finally:
                if conn:
                    cursor.close()
                    conn.close()
                # Check that consumer status, in case we need to stop
                conn_check, cursor_check = get_db_connection() # Open separate connection
                cursor_check.execute("SELECT is_running FROM rabbitmq_consumer_control LIMIT 1")
                result = cursor_check.fetchone()
                if result and not result[0]:
                    logging.info("Stop signal detected in callback. Stopping consuming.")
                    stop_consuming = True
                    ch.stop_consuming()
                    #cursor_check.execute("DELETE FROM rabbitmq_consumer_control")
                    #conn_check.commit()
                conn_check.close()

        channel.basic_qos(prefetch_count=1)  # Process one message at a time
        rabbitmq_modify_consumer_status(status=True) # Update to Start status (in progress)
        channel.basic_consume(queue=rabbitmq_queue, on_message_callback=callback, auto_ack=False)

        logging.info('f" [*] Waiting for messages in {rabbitmq_queue}...')
        channel.start_consuming()  # This will block until the connection is closed

    except pika.exceptions.AMQPConnectionError as e:
        logging.info(f"Error connecting to RabbitMQ: {e}")
    except Exception as e:
        logging.info(f"An unexpected error occurred: {e}")
    finally:
        if 'connection' in locals() and connection.is_open:
            connection.close()

# Consume for short period of time (here is for 1 minute)
def consume_one(**kwargs):
    rabbitmq_queue = kwargs.get('queue_id','info_test_queue')
    dag_run = kwargs['dag_run']
    dag_name = dag_run.dag_id
    consumption_duration_seconds = 60  # Consume for 1 minute

    messages = []
    stop_event = Event()

    # Here we push messages to list to process them all together later
    def callback(ch, method, properties, body):
        messages.append(body.decode())
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def consume():
        try:
            credentials =  pika.PlainCredentials('admin', os.getenv('RABBITMQ_PASSWORD'))
            connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq',credentials=credentials))
            channel = connection.channel()

            channel.basic_qos(prefetch_count=1)  # Process one message at a time
            channel.basic_consume(queue=rabbitmq_queue, on_message_callback=callback, auto_ack=False)

            logging.info('f" [*] Waiting for messages in {rabbitmq_queue}...')
            channel.start_consuming()  # This will block until the connection is closed

        except pika.exceptions.AMQPConnectionError as e:
            logging.info(f"Error connecting to RabbitMQ: {e}")
        except Exception as e:
            logging.info(f"An unexpected error occurred: {e}")
        finally:
            if 'connection' in locals() and connection.is_open:
                connection.close()

    consumer_thread = Thread(target=consume)
    consumer_thread.daemon = True  # Allow the main thread to exit even if this is running
    consumer_thread.start()

    # Wait for the specified duration
    time.sleep(consumption_duration_seconds)
    logging.info(" [*] Finished waiting, requesting consumer to stop.")

    # Try to gracefully stop consuming (this might not be immediate)
    # The 'consume' function will exit when no more messages are being processed
    # after the timeout.
    stop_event.wait(timeout=5) # Give a short time for the thread to finish

    logging.info(f" [*] Received {len(messages)} messages.")
    kwargs['ti'].xcom_push(key='rabbitmq_received_messages', value=messages)

def insert_xcom_to_postgres(**kwargs):
    """
    Retrieves messages from XCom, creates a Pandas DataFrame,
    and inserts the data into PostgreSQL.
    """
    # Get some values
    ti = kwargs['task_instance']
    consumer_task_id = kwargs['consumer_task_id']
    dag_id = ti.dag_id
    POSTGRES_TABLE = os.getenv('POSTGRES_RABBITMQ_TABLE')
    column_names = ['message_data', 'dag_id']

    received_messages = kwargs['ti'].xcom_pull(task_ids=consumer_task_id, key='rabbitmq_received_messages')
    data_to_insert = [(msg, dag_id) for msg in received_messages]

    if received_messages:
        try:
            # Establish connection
            conn, cursor = get_db_connection()
            
            # Prepare the SQL INSERT statement with placeholders
            columns = ', '.join(column_names)
            placeholders = ', '.join(['%s'] * len(column_names))
            insert_sql = f"INSERT INTO {POSTGRES_TABLE} ({columns}) VALUES ({placeholders})"
            logging.info(insert_sql)
            logging.info(data_to_insert)
            # Execute the batch insert
            extras.execute_batch(cursor, insert_sql, data_to_insert)
            conn.commit()
            logging.info(f"Successfully inserted {len(data_to_insert)} rows into {POSTGRES_TABLE}")

        except psycopg2.Error as e:
            logging.info(f"PostgreSQL error: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                cursor.close()
                conn.close()
    else:
        logging.info("No messages received to insert.")