ARG AIRFLOW_VERSION

FROM apache/airflow:${AIRFLOW_VERSION}
ARG CONSTRAINTS_URL

ENV CONSTRAINTS_URL=${CONSTRAINTS_URL}

USER root

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    && rm -rf /var/lib/apt/lists/*

USER airflow

RUN pip install --upgrade pip
RUN pip install apache-airflow[redis]==${AIRFLOW_VERSION} --constraint "${CONSTRAINTS_URL}"
RUN pip install apache-airflow[celery]==${AIRFLOW_VERSION} --constraint "${CONSTRAINTS_URL}" 

# Або просто:
# RUN pip install apache-airflow[redis]

# Додаткові пакети Python, якщо потрібно
RUN pip install --no-cache-dir \
    apache-airflow-providers-celery \
    psycopg2-binary

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt --constraint "${CONSTRAINTS_URL}"

# Створення користувача airflow (якщо його ще немає; в офіційному образі він вже є)
# RUN useradd -ms /bin/bash airflow

# Зміна прав власності на важливі папки (якщо потрібно)
# RUN chown -R airflow:airflow /opt/airflow/dags /opt/airflow/logs /opt/airflow/plugins

# Копіювання ваших DAGs (якщо є)
# COPY --chown=airflow:airflow dags /opt/airflow/dags

# Копіювання ваших плагінів (якщо є)
# COPY --chown=airflow:airflow plugins /opt/airflow/plugins

USER root

# Ensure Airflow directories exist and have correct permissions
RUN mkdir -p /opt/airflow/dags /opt/airflow/plugins /opt/airflow/logs \
    && chown -R 50000:50000 /opt/airflow

# Copy entrypoint script and make it executable
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch back to airflow user
USER airflow

ENTRYPOINT ["/entrypoint.sh"]