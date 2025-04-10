# Use the iceberg-rest base image
FROM tabulario/iceberg-rest:1.6.0

# Switch to the root user to have permissions to install packages
USER root

# Update package lists and install sqlite3 - in case you want use this db for internal rest catalog db
#RUN apt-get update && apt-get install -y sqlite3

# Switch back to the iceberg user
USER iceberg