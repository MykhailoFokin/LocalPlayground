#!/bin/bash
set -e

# Перевірка, чи база даних вже ініціалізована
if ! airflow db check || [[ "$?" -ne 0 ]]; then
  echo "Ініціалізація бази даних Airflow..."
  airflow db migrate
  echo "Ініціалізація бази даних Airflow завершена."
fi

# Запуск вказаного процесу Airflow
if [[ "$1" == "webserver" ]]; then
  echo "Запуск веб-сервера Airflow..."
  exec airflow webserver
elif [[ "$1" == "scheduler" ]]; then
  echo "Запуск scheduler'а Airflow..."
  exec airflow scheduler
elif [[ "$1" == "worker" ]]; then
  echo "Запуск воркера Airflow..."
  exec airflow celery worker
else
  echo "Невідомий процес Airflow: $1"
  exit 1
fi