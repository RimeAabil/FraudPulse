import csv
import json
import time
import os
import logging
from kafka import KafkaProducer
from kafka.errors import NoBrokersAvailable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_kafka_producer(broker, max_retries=10):
    retries = 0
    backoff = 2
    while retries < max_retries:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[broker],
                value_serializer=lambda x: json.dumps(x).encode('utf-8')
            )
            logger.info("Successfully connected to Kafka.")
            return producer
        except NoBrokersAvailable:
            logger.warning(f"Kafka not available. Retrying in {backoff} seconds...")
            time.sleep(backoff)
            retries += 1
            backoff *= 2
    logger.error("Failed to connect to Kafka after multiple retries.")
    raise Exception("Kafka connection failed.")

def main():
    broker = os.environ.get('KAFKA_BROKER', 'localhost:9092')
    topic = os.environ.get('KAFKA_TOPIC', 'fraud-transactions')
    delay_str = os.environ.get('STREAM_DELAY_SECONDS', '0.1')
    delay = float(delay_str)

    producer = create_kafka_producer(broker)
    
    csv_file = 'paysim.csv'
    if not os.path.exists(csv_file):
        logger.error(f"Data file {csv_file} not found.")
        return

    logger.info(f"Starting to produce messages to topic {topic}...")
    
    try:
        with open(csv_file, mode='r') as file:
            reader = csv.DictReader(file)
            count = 0
            for row in reader:
                try:
                    row['step'] = int(row['step'])
                    row['amount'] = float(row['amount'])
                    row['oldbalanceOrg'] = float(row['oldbalanceOrg'])
                    row['newbalanceOrig'] = float(row['newbalanceOrig'])
                    row['oldbalanceDest'] = float(row['oldbalanceDest'])
                    row['newbalanceDest'] = float(row['newbalanceDest'])
                    if 'isFraud' in row:
                        row['isFraud'] = int(row['isFraud'])
                    if 'isFlaggedFraud' in row:
                        row['isFlaggedFraud'] = int(row['isFlaggedFraud'])
                except ValueError as ve:
                    logger.warning(f"Skipping row due to ValueError: {ve}")
                    continue
                
                producer.send(topic, value=row)
                count += 1
                if count % 1000 == 0:
                    logger.info(f"Produced {count} messages...")
                time.sleep(delay)
    except KeyboardInterrupt:
        logger.info("Production interrupted by user.")
    except Exception as e:
        logger.error(f"Error producing messages: {e}")
    finally:
        producer.flush()
        producer.close()
        logger.info("Producer closed.")

if __name__ == '__main__':
    main()
