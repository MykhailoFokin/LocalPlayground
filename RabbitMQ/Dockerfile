FROM rabbitmq:4.0.8-management
COPY rabbitmq.conf /etc/rabbitmq/
COPY definitions.json /etc/rabbitmq/
ENV RABBITMQ_CONFIG_FILE=/etc/rabbitmq/rabbitmq.conf
ENV RABBITMQ_DEFINITIONS_FILE=/etc/rabbitmq/definitions.json
EXPOSE 5672 15672