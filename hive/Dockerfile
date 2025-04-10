FROM apache/hive:4.0.1

# 3.4.1
ENV HADOOP_VERSION=3.3.2 
# 1.12.782
ENV AWS_SDK_VERSION=1.11.1026

# PostgreSQL client
USER root
RUN apt-get update && \
    apt-get install -y postgresql-client && \
    apt-get install -y wget --no-install-recommends && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Download hadoop-aws JAR
RUN wget "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/${HADOOP_VERSION}/hadoop-aws-${HADOOP_VERSION}.jar" -P /opt/hive/lib/

# Download aws-java-sdk-bundle JAR
RUN wget "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/${AWS_SDK_VERSION}/aws-java-sdk-bundle-${AWS_SDK_VERSION}.jar" -P /opt/hive/lib/

# Clean up wget
RUN rm -rf /tmp/*

# Copy initialization script
COPY init_metastore.sh /opt/hive/bin/init_metastore.sh
RUN chmod +x /opt/hive/bin/init_metastore.sh

# Start script if required
#CMD ["/opt/hive/bin/init_metastore.sh"]
