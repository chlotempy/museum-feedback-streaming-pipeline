from database_functions import (connect_to_database, load_exhibition_mapping,
                                load_rating_mapping, load_request_mapping,
                                insert_kafka_record,
                                insert_kafka_records_batch)
from validator_functions import validate_and_clean_record
import logging
from datetime import datetime
from os import environ
from dotenv import load_dotenv
from confluent_kafka import Consumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kafka_consumer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def consume_data_batches(consumer: Consumer):
    """Generator that yields batches of cleaned records."""
    batch_records = []
    batch_start_time = datetime.now()
    batch_timeout_secs = 10
    max_batch_size = 100

    message_count = 0
    cleaned_count = 0
    skipped_count = 0

    try:
        while True:
            msg = consumer.poll(1)

            if msg is not None:
                message_count += 1

                if msg.error():
                    logger.error(f"Kafka error: {msg.error()}")
                    skipped_count += 1
                else:
                    decoded_msg = msg.value().decode('utf-8')
                    cleaned_record = validate_and_clean_record(decoded_msg)

                    if cleaned_record:
                        cleaned_count += 1
                        batch_records.append(cleaned_record)
                    else:
                        skipped_count += 1

            # Check if batch ready
            elapsed_time = (datetime.now() - batch_start_time).total_seconds()
            if (len(batch_records) >= max_batch_size or
                    elapsed_time >= batch_timeout_secs):

                if batch_records:
                    # LOG BATCH YIELD IN GENERATOR
                    logger.info(
                        f"Yielding batch of {len(batch_records)} records after {elapsed_time:.1f}s")
                    yield batch_records

                    batch_records = []
                    batch_start_time = datetime.now()

            # Progress logging in generator
            if message_count % 100 == 0:
                logger.info(
                    f"Polling stats - Total: {message_count}, Cleaned: {cleaned_count}, Skipped: {skipped_count}")

    finally:
        if batch_records:
            logger.info(
                f"Yielding final batch of {len(batch_records)} records")
            yield batch_records


def process_batches(consumer: Consumer) -> None:
    """Process batches from Kafka consumer."""
    logger.info("Starting batch processor...")

    conn = connect_to_database()
    with conn:
        with conn.cursor() as cursor:
            exhibitions = load_exhibition_mapping(cursor)
            ratings = load_rating_mapping(cursor)
            requests = load_request_mapping(cursor)

    inserted_count = 0
    duplicate_count = 0

    try:
        for batch in consume_data_batches(consumer):
            # LOG BATCH PROCESSING
            logger.info(f"Processing batch of {len(batch)} records")

            with conn.cursor() as cursor:
                batch_inserted, batch_duplicates = insert_kafka_records_batch(
                    cursor, batch, exhibitions, ratings, requests)
                inserted_count += batch_inserted
                duplicate_count += batch_duplicates
            conn.commit()

            # LOG BATCH COMPLETION
            logger.info(
                f"Batch complete. Total inserted: {inserted_count}, Duplicates: {duplicate_count}")

    except KeyboardInterrupt:
        logger.info("Consumer interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        logger.info(
            f"Processor stopped. Final - Inserted: {inserted_count}, Duplicates: {duplicate_count}")
        consumer.close()
        conn.close()


if __name__ == "__main__":

    logger.info("Kafka Consumer starting up")

    load_dotenv()
    logger.info("Environment variables loaded")

    try:
        consumer = Consumer({
            "bootstrap.servers": environ["BOOTSTRAP_SERVERS"],
            "group.id": "c26-chloe-final-2",
            "auto.offset.reset": "earliest",
            'security.protocol': environ["SECURITY_PROTOCOL"],
            'sasl.mechanism': environ["SASL_MECHANISM"],
            'sasl.username': environ["USERNAME"],
            'sasl.password': environ["PASSWORD"],
            'log_level': 7
        })
        logger.info("Kafka consumer created successfully")

        TOPIC = "lmnh"
        consumer.subscribe([TOPIC])
        logger.info(f"Subscribed to topic: {TOPIC}")

        process_batches(consumer)

    except KeyError as e:
        logger.error(f"Missing environment variable: {e}")
    except Exception as e:
        logger.error(f"Failed to create consumer: {e}", exc_info=True)
