#!/bin/bash

POSTGRES_HOST="${HIVE_POSTGRES_HOST:-postgres}"
POSTGRES_PORT="${HIVE_POSTGRES_PORT:-5432}"
POSTGRES_HIVE_USER="${HIVE_CONF_javax_jdo_option_ConnectionUserName}"
POSTGRES_HIVE_PASSWORD="${HIVE_CONF_javax_jdo_option_ConnectionPassword}"
POSTGRES_HIVE_DB="${HIVE_POSTGRES_DB}"

JDBC_URL="${HIVE_CONF_javax_jdo_option_ConnectionURL}"
JDBC_DRIVER="${HIVE_CONF_javax_jdo_option_ConnectionDriverName}"

echo "JDBC_URL: $JDBC_URL"

get_schema_version() {
  PGPASSWORD="$POSTGRES_HIVE_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_HIVE_USER" -d "$POSTGRES_HIVE_DB" -tAc "SELECT \"SCHEMA_VERSION\" FROM \"VERSION\";"
  #PGPASSWORD="$POSTGRES_HIVE_PASSWORD" psql -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U "$POSTGRES_HIVE_USER" -d "$POSTGRES_HIVE_DB" -tAc "SELECT SCHEMA_VERSION FROM VERSION;"
}

current_version=$(get_schema_version)
if [ -n "$current_version" ]; then
  echo "$(date) - Current Hive Metastore schema version: $current_version"
else
  echo "$(date) - Initializing Hive Metastore schema..."
  # Initialize the Hive Metastore schema using the PostgreSQL database type and specifying the configuration file
  /opt/hive/bin/schematool -initSchema -dbType postgres postgres -verbose\
    -url "$JDBC_URL" \
    -driver "$JDBC_DRIVER" \
    -userName "$POSTGRES_HIVE_USER" \
    -passWord "$POSTGRES_HIVE_PASSWORD"
  # Check if the schema initialization was successful
  if [ $? -eq 0 ]; then
    echo "$(date) - Hive Metastore schema initialized successfully."
  else
    echo "$(date) - Error initializing Hive Metastore schema."
    exit 1
  fi
fi

# Start the Hive Metastore service
echo "$(date) - Starting Hive Metastore..."
echo "$(date) - Using JDBC: $JDBC_URL"
/opt/hive/bin/hive --service metastore #-hiveconf hive.metastore.warehouse.dir=s3a://hive_data/