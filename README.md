# LocalPlayground

**LocalPlayground** is a local development environment for experimenting with data engineering tools. It includes a collection of preconfigured services running via Docker Compose, allowing you to prototype and test data workflows on your machine.

## Technologies Included

This setup includes configurations for the following services, organized into profiles and default services:

**Default Services (Always Started):**

* **Airflow:** A platform to programmatically author, schedule, and monitor workflows.
* **PostgreSQL:** A powerful, open-source relational database system, used as the metadata database for Airflow.
* **Mailhog:** A fake SMTP server for easy email testing.

**`trino-party` Profile Services:**

* **Trino:** A fast, distributed SQL query engine for big data analytics.
* **Minio:** A high-performance, S3 compatible object storage service.
* **Hive Metastore:** A central repository for Apache Hive metadata.
* **Iceberg REST Catalog:** A RESTful catalog service for Apache Iceberg tables.

**`rabbitmq` Profile Services:**
* **RabbitMQ:** A widely deployed open-source message broker.

## 🧰 Included Services

| Service                  | Purpose                                      | Port(s)        |
|--------------------------|----------------------------------------------|----------------|
| **Airflow**              | Scheduler                                    | `8080`         |
| **Trino**                | Distributed SQL engine                       | `8082`         |
| **MinIO**                | S3-compatible object storage                 | `9000`, `9001` |
| **PostgreSQL**           | Relational database for metadata or testing  | `5432`         |
| **Hive Metastore**       | Metastore                                    | `9083`         |
| **Iceberg REST Catalog** | REST-based catalog for Apache Iceberg        | `8181`         |
| **Mailhog**              | SMTP-mock service                            | `1025`, `8025` |
| **RabbitMQ**             | Message broker                               | `5672`, `15672`|

## 🚀 Getting Started

### Prerequisites

* **Docker:** Ensure you have Docker installed on your local machine. Installation instructions can be found here: [https://docs.docker.com/engine/install/](https://docs.docker.com/engine/install/)
* **Docker Compose:** Docker Compose is usually installed along with Docker Desktop. For separate installations, see: [https://docs.docker.com/compose/install/](https://docs.docker.com/compose/install/)

### Launch the environment

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/MykhailoFokin/LocalPlayground.git](https://github.com/MykhailoFokin/LocalPlayground.git)
    cd LocalPlayground
    ```

2.  **Start the Services:**

    * **Default Services (Airflow, PostgreSQL, Mailhog):**
        ```bash
        docker-compose up -d
        ```
        This command starts the Airflow webserver and scheduler, along with the PostgreSQL database required for Airflow's metadata.

    * **`trino-party` Profile (Trino, Iceberg-rest catalog, Hive metastore, Minio):**
        ```bash
        docker-compose --profile trino-party up -d
        ```
        This command starts the services defined in the `trino-party` profile in addition to the default services.

    * **`rabbitmq` Profile (RabbitMQ):**
        ```bash
        docker-compose --profile rabbitmq up -d
        ```
        This command starts all services defined in the `rabbitmq` profile.

    * **All together:**
        ```bash
        docker-compose --profile trino-party --profile rabbitmq up -d
        ```
        This command starts all services defined in the `rabbitmq` profile.

### Accessing the Services

Once the services are running, you can access them using the following default configurations:

* **Airflow:**
    * **Web UI:** Typically accessible at `http://localhost:8080`.
    * **Default User:** `airflow`
    * **Default Password:** `airflow` (It is highly recommended to change these credentials.)

* **PostgreSQL (here for Airflow, but each service has own db and credentials):**
    * **Hostname:** `postgres`
    * **Port:** `5432`
    * **Database:** `airflow_db`
    * **User:Password** You can find at .env file
    * **API Port:** `9000`

* **Mailhog (fake email server):**
    * **Web UI:** Accessible at `http://localhost:8025`.

* **RabbitMQ (`rabbitmq` profile):**
    * **Management UI:** Accessible at `http://localhost:15672`.
    * **Default User:** `admin`
    * **Default Password:** `test` (It is highly recommended to change these credentials.)
    * **AMQP Port:** `5672`

* **Trino (`trino-party` profile):**
    * **Web UI:** Accessible at `http://localhost:8082`.
    * **JDBC/CLI:** Connect using the hostname `trino` on port `8082`.

* **Minio (`trino-party` profile):**
    * **Web UI:** Accessible at `http://localhost:9001`.
    * **Access Key:** `admin`
    * **Secret Key:** `password` (It is highly recommended to change these credentials.)

* **Hive Metastore (`trino-party` profile):**
    * **Hostname:** `hive-metastore`
    * **Port:** `9083` (Thrift port for Hive Metastore access).

* **Iceberg REST Catalog (`trino-party` profile):**
    * **API URL:** Typically accessible at `http://localhost:8181`. Refer to the Iceberg REST Catalog documentation for specific API endpoints.

## Configuration

The service configurations are defined in the `docker-compose.yml` file. You can modify this file to adjust ports, environment variables, volumes, and other settings according to your needs. Pay attention to the profile directives (`profiles:`) to understand which services are started with which commands.

## Stopping the Services

To stop and remove the containers, networks, and volumes defined in the `docker-compose.yml` file, considering the active profiles:

* **All running services (regardless of profile):**
    ```bash
    docker-compose down
    ```
* **Specific profiles:**
    ```bash
    docker-compose --profile trino-party down
    docker-compose --profile rabbitmq down
    ```
    (Note: You might need to run `docker-compose down` without any profiles first to ensure all dependencies are stopped correctly).
    ```
* **All together:**
    ```bash
    docker compose --profile "*" down
    ```
    (Note: You might need to run `docker-compose down` without any profiles first to ensure all dependencies are stopped correctly).

To stop or start specific profiles without removing them, use `docker-compose stop --profile <profile>` or `docker-compose start --profile <profile>`.

## 🗃️ Folder Structure

The repository structure is organized to keep different components of the local development environment logically separated:

```plaintext
LocalPlayground/
├── dags/
│   ├── Hive_Postgres_Iceberg.py
│   └── rabbitmq_sender.py
├── plugins/
│   └── ... (Custom Airflow plugins, if any)
├── templates/
│   └── dag_report_email.html
├── utils/
│   ├── email/
│   │   └── CustomEmailOperator.py
│   └── rabbitmq/
│       └── source.py
├── docker-compose.yml
├── .dockerignore
└── README.md
```

## 📌 Notes

- Credentials, ports, and volumes can be adjusted in the `.env` file.
- This environment is for **local testing only** and is not production-ready.

## 💡 Use Cases

- Query Iceberg tables via **Trino**
- Use **MinIO** as a data lake storage backend
- Test data federation using **Trino** with **PostgreSQL**
- Manage metadata catalogs through the **Iceberg REST Catalog**
- Debug local SQL workflows across multiple engines
- Prototype ELT pipelines with a local stack

## Contributing

Contributions to this repository are welcome. If you have suggestions for improvements, new service configurations, or bug fixes, please feel free to open an issue or submit a pull request.

## License

This project is open-source and available under the [MIT License](https://www.google.com/search?q=LICENSE) (if a `LICENSE` file is present in the repository). You are free to use, modify, and distribute it according to the terms of the license. If no `LICENSE` file is present, the code is under the default copyright laws, and explicit permission is required for use.

## 👨‍💻 Author

**Mykhailo Fokin**  
GitHub: [@MykhailoFokin](https://github.com/MykhailoFokin)

-----

**Note:** Please refer to the specific documentation of each technology (Airflow, PostgreSQL, Trino, RabbitMQ, Minio, Iceberg, Hive) for more detailed information on their usage and configuration options. This `docker-compose` setup provides a basic environment for local development. Remember to adjust configurations and credentials for non-development environments.