from airflow import DAG
from airflow.operators.email import EmailOperator
from airflow.operators.dummy import DummyOperator
from utils.email import CustomEmailOperator
from airflow.decorators import task
from airflow.configuration import conf
import psycopg2
from trino.dbapi import connect
import os
from datetime import datetime
import logging


with DAG(
    dag_id='email_test_dag',
    start_date=datetime(2025, 1, 1),
    schedule_interval=None,
    catchup=False,
    render_template_as_native_obj = True,
    template_searchpath = os.path.join(conf['core']['dags_folder'], "templates"),
    tags=['basic', 'medium', 'email', 'Mailhog'],
) as dag:
    
    # Default email message without any formatting
    basic_email = EmailOperator(
        task_id='basic_email',
        to='test@example.com',
        subject='Test Email from Airflow',
        html_content='<p>This is a test email sent from Airflow via MailHog.</p>',
    )

    @task
    def get_infra_info():
        try:
            step = 'PostgreSQL'
            result = []

            logging.info("Connecting to Postgres")
            pg_conn = psycopg2.connect(
                host=os.getenv('POSTGRES_HOST'),
                port=os.getenv('POSTGRES_PORT'),
                database=os.getenv('POSTGRES_DB'),
                user=os.getenv('POSTGRES_USER'),
                password=os.getenv('POSTGRES_PASSWORD')
            )
            pg_cursor = pg_conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            pg_cursor.execute("SELECT version() as version")
            pg_result = pg_cursor.fetchone()
            result.append({'target': step, 'command': 'version', 'result': pg_result['version']})

            logging.info("Connecting to Trino")
            step = 'Trino'
            trino_conn = connect(
                host=os.getenv('TRINO_HOST', default='localhost'),
                port=os.getenv('TRINO_PORT'),  # Default Trino port
                user=os.getenv('TRINO_USER'),
                catalog='system',
                schema='information_schema'
            )
            trino_cursor = trino_conn.cursor()

            # Now you can execute Trino SQL queries
            trino_cursor.execute("SELECT version() as version")
            trino_result = trino_cursor.fetchone()
            result.append({'target': step, 'command': 'version', 'result': trino_result[0]})
            
            logging.info("Return results.")
            return result

        except Exception as e:
            if step == 'PostgreSQL':
                pg_conn.rollback()
            logging.info(f"Error with {step}: {e}")
            raise
        finally:
            if pg_conn:
                pg_cursor.close()
                pg_conn.close()
            if trino_conn:
                trino_conn.close()

    # Email with custom formatting and input values
    templated_email = CustomEmailOperator(
        task_id = 'templated_email',
        to = 'test@example.com',
        subject = 'Test Custom Email from Airflow',
        html_content = 'templates/table_email.html',
        params = {
            "content": {
                "paragraph": "Data checks by DAG run ID <strong>{{ run_id }}</strong>",
                "messages": '{{ ti.xcom_pull(task_ids="get_infra_info", key="return_value") }}',
            },
            "style": {
                "main_color": "default"
            }
        }
    )

    templated_email_success = CustomEmailOperator(
        task_id = 'templated_email_success',
        to = 'test@example.com',
        subject = 'DAG finished successfully',
        html_content = 'templates/base.html',
        params = {
            "style": {
                "main_color": "success"
            }
        }
    )

    basic_email >> templated_email_success
    get_infra_info() >> templated_email >> templated_email_success