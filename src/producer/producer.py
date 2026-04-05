import csv
import json
import time
import os
import logging
import uuid
from confluent_kafka import Producer, KafkaException
from prometheus_client import start_http_server, Counter, Histogram, Gauge

# Prometheus Metrics
RECORDS_PRODUCED = Counter('fraudpulse_records_produced_total', 'Total number of records produced')
PRODUCE_ERRORS = Counter('fraudpulse_produce_errors_total', 'Total number of record production errors')
BATCH_SIZE = Gauge('fraudpulse_current_batch_size', 'Current batch size of the producer')
DELIVERY_LATENCY = Histogram('fraudpulse_delivery_latency_seconds', 'Time taken to deliver a record')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def delivery_report(err, msg, start_time):
    """ Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush(). """
    latency = time.time() - start_time
    DELIVERY_LATENCY.observe(latency)
    
    if err is not None:
        logger.error(f'Message delivery failed: {err}')
        PRODUCE_ERRORS.inc()
    else:
        RECORDS_PRODUCED.inc()

def create_kafka_producer(brokers, max_retries=10):
    retries = 0
    backoff = 2
    while retries < max_retries:
        try:
            conf = {
                'bootstrap.servers': brokers,
                'acks': 'all',
                'enable.idempotence': True,
                'compression.type': os.environ.get('PRODUCER_COMPRESSION', 'lz4'),
                'linger.ms': int(os.environ.get('PRODUCER_LINGER_MS', '10')),
                'batch.size': int(os.environ.get('PRODUCER_BATCH_SIZE', '32768')),
                'message.max.bytes': 1000000,
                'queue.buffering.max.messages': 100000,
                'retry.backoff.ms': 100
            }
            producer = Producer(conf)
            # Test connection by trying to fetch metadata
            producer.list_topics(timeout=5)
            logger.info(f"Successfully connected to Kafka brokers: {brokers}")
            return producer
        except Exception as e:
            logger.warning(f"Kafka not available ({e}). Retrying in {backoff} seconds...")
            time.sleep(backoff)
            retries += 1
            backoff *= 2
    logger.error("Failed to connect to Kafka after multiple retries.")
    raise Exception("Kafka connection failed.")

def main():
    start_http_server(8001)  # Export Prometheus metrics
    
    brokers = os.environ.get('KAFKA_BROKER', 'localhost:9092')
    topic = os.environ.get('KAFKA_TOPIC', 'fraud-transactions')
    delay = float(os.environ.get('STREAM_DELAY_SECONDS', '0.01'))
    
    producer = create_kafka_producer(brokers)
    
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
                    # Parse and clean types
                    payload = {
                        'step': int(row['step']),
                        'type': row['type'],
                        'amount': float(row['amount']),
                        'nameOrig': row['nameOrig'],
                        'oldbalanceOrg': float(row['oldbalanceOrg']),
                        'newbalanceOrig': float(row['newbalanceOrig']),
                        'nameDest': row['nameDest'],
                        'oldbalanceDest': float(row['oldbalanceDest']),
                        'newbalanceDest': float(row['newbalanceDest']),
                        'isFraud': int(row['isFraud']) if 'isFraud' in row and row['isFraud'] else 0,
                        'isFlaggedFraud': int(row['isFlaggedFraud']) if 'isFlaggedFraud' in row and row['isFlaggedFraud'] else 0
                    }
                    
                    start_time = time.time()
                    
                    # Produce async
                    # We use a lambda to pass the start_time to the delivery report
                    producer.produce(
                        topic, 
                        key=payload['nameOrig'],
                        value=json.dumps(payload).encode('utf-8'),
                        callback=lambda err, msg, st=start_time: delivery_report(err, msg, st)
                    )
                    
                    # Serve delivery reports
                    producer.poll(0)
                    
                    count += 1
                    if count % 100 == 0:
                        logger.info(f"🚀 Produced {count} messages to Kafka...")
                        producer.flush() # Ensure all messages are sent
                    
                    if delay > 0:
                        time.sleep(delay)
                        
                except ValueError as ve:
                    logger.warning(f"Skipping row due to ValueError: {ve}")
                    continue
                except KafkaException as e:
                    if e.args[0].fatal():
                        logger.critical(f"FATAL Kafka Error: {e}. Producer must be recreated.")
                        raise e # This will trigger the main exception handler and exit
                    else:
                        logger.error(f"Non-fatal Kafka error: {e}")
                except Exception as e:
                    logger.error(f"Error preparing message: {e}")
                    
    except KeyboardInterrupt:
        logger.info("Production interrupted by user.")
    except Exception as e:
        logger.error(f"Fatal error producing messages: {e}")
    finally:
        logger.info("Flushing remaining messages...")
        producer.flush()
        logger.info("Producer closed.")

if __name__ == '__main__':
    main()
