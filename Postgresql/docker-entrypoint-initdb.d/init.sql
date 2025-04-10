CREATE USER airflow WITH PASSWORD 'airflow';
CREATE DATABASE airflow_db OWNER airflow;
GRANT ALL PRIVILEGES ON DATABASE airflow_db TO airflow;

CREATE DATABASE user_db OWNER postgres;

-- This one required for iceberg-rest 
CREATE USER iceberg_rest_user  WITH PASSWORD 'iceberg_rest_password';
CREATE DATABASE iceberg_rest_db OWNER iceberg_rest_user;
GRANT ALL PRIVILEGES ON DATABASE iceberg_rest_db TO iceberg_rest_user;

-- This one required for trino as target 
CREATE USER trino_user  WITH PASSWORD 'trino_password';
CREATE DATABASE trino_db OWNER trino_user;
GRANT ALL PRIVILEGES ON DATABASE trino_db TO trino_user;

-- This one required for hive
CREATE USER hive_metastore_user  WITH PASSWORD 'hive_metastore_password';
CREATE DATABASE hive_metastore_db OWNER hive_metastore_user;
GRANT ALL PRIVILEGES ON DATABASE hive_metastore_db TO hive_metastore_user;