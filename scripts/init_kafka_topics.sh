#!/bin/bash
set -e

# Environment variables are provided by Docker env_file

echo "Waiting for Kafka to be ready..."
cub kafka-ready -b kafka-1:29092 1 60

echo "Creating standard topics..."

# fraud-transactions (Main input topic, 6 partitions, RF 3)
kafka-topics --bootstrap-server kafka-1:29092 --create --if-not-exists \
  --topic ${KAFKA_TOPIC:-fraud-transactions} \
  --partitions ${KAFKA_NUM_PARTITIONS:-6} \
  --replication-factor ${KAFKA_REPLICATION_FACTOR:-3}

# fraud-transactions-dlq (Dead Letter Queue, 3 partitions, RF 3)
kafka-topics --bootstrap-server kafka-1:29092 --create --if-not-exists \
  --topic ${KAFKA_DLQ_TOPIC:-fraud-transactions-dlq} \
  --partitions 3 \
  --replication-factor ${KAFKA_REPLICATION_FACTOR:-3}

# model-predictions (Scored results for downstream, 6 partitions, RF 3)
kafka-topics --bootstrap-server kafka-1:29092 --create --if-not-exists \
  --topic ${KAFKA_PREDICTIONS_TOPIC:-model-predictions} \
  --partitions ${KAFKA_NUM_PARTITIONS:-6} \
  --replication-factor ${KAFKA_REPLICATION_FACTOR:-3}

# pipeline-metrics (Internal low volume, 1 partition)
kafka-topics --bootstrap-server kafka-1:29092 --create --if-not-exists \
  --topic ${KAFKA_METRICS_TOPIC:-pipeline-metrics} \
  --partitions 1 \
  --replication-factor ${KAFKA_REPLICATION_FACTOR:-3}

echo "Successfully created topics."
kafka-topics --bootstrap-server kafka-1:29092 --list
