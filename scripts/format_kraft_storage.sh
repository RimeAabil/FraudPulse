#!/bin/sh
set -e

# Copy the mounted read-only config to a writable temporary file
cp /etc/kafka/kafka.properties /tmp/kafka.properties

# Replace placeholders with environment variables defined in the docker-compose/env file
# We use a simple sed replacement for each variable
sed -i "s/\${KAFKA_CLUSTER_ID}/$KAFKA_CLUSTER_ID/g" /tmp/kafka.properties
sed -i "s/\${KAFKA_1_EXTERNAL_PORT}/$KAFKA_1_EXTERNAL_PORT/g" /tmp/kafka.properties
sed -i "s/\${KAFKA_2_EXTERNAL_PORT}/$KAFKA_2_EXTERNAL_PORT/g" /tmp/kafka.properties
sed -i "s/\${KAFKA_3_EXTERNAL_PORT}/$KAFKA_3_EXTERNAL_PORT/g" /tmp/kafka.properties

# Format storage using the generated config
# The --ignore-formatted flag allows the container to restart without error if already formatted
kafka-storage format --ignore-formatted -t $KAFKA_CLUSTER_ID -c /tmp/kafka.properties

# Start Kafka with the processed configuration
echo "Starting Kafka with processed configuration..."
exec kafka-server-start /tmp/kafka.properties
