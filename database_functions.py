import logging
import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor
from dotenv import dotenv_values

logger = logging.getLogger(__name__)


def connect_to_database(config_path: str = ".env") -> psycopg2.extensions.connection:
    """Connect to RDS database using credentials from .env file."""
    config = dotenv_values(config_path)
    logger.info(
        f"Connecting to database {config['DATABASE_NAME']} on {config['DATABASE_IP']}")

    return psycopg2.connect(
        user=config["DATABASE_USERNAME"],
        password=config["DATABASE_PASSWORD"],
        host=config["DATABASE_IP"],
        port=config["DATABASE_PORT"],
        database=config["DATABASE_NAME"],
        cursor_factory=RealDictCursor,
    )


def load_exhibition_mapping(cursor) -> dict:
    """Fetch exhibition ID mapping by site number (public_id)."""
    cursor.execute("SELECT public_id, exhibition_id FROM exhibition")
    mapping = {row["public_id"]: row["exhibition_id"]
               for row in cursor.fetchall()}
    logger.debug(f"Loaded {len(mapping)} exhibitions from database")
    return mapping


def load_rating_mapping(cursor) -> dict:
    """Fetch rating ID mapping by rating value (0-4)."""
    cursor.execute("SELECT rating_value, rating_id FROM rating")
    mapping = {row["rating_value"]: row["rating_id"]
               for row in cursor.fetchall()}
    logger.debug(f"Loaded {len(mapping)} ratings from database")
    return mapping


def load_request_mapping(cursor) -> dict:
    """Fetch request ID mapping by request value."""
    cursor.execute("SELECT request_value, request_id FROM request")
    mapping = {row["request_value"]: row["request_id"]
               for row in cursor.fetchall()}
    logger.debug(f"Loaded {len(mapping)} requests from database")
    return mapping


def insert_interaction(cursor, table: str, id_column: str, id_value: int, exhibition_id: int, event_at: str) -> bool:
    """
    Generic insert interaction with duplicate check.

    Returns True if inserted, False if duplicate.
    """
    query = sql.SQL("""
        INSERT INTO {table} ({id_column}, exhibition_id, event_at)
        SELECT %s, %s, %s
        WHERE NOT EXISTS (
            SELECT 1 FROM {table}
            WHERE {id_column} = %s AND exhibition_id = %s AND event_at = %s
        )
    """).format(table=sql.Identifier(table), id_column=sql.Identifier(id_column))

    cursor.execute(query, (id_value, exhibition_id, event_at,
                   id_value, exhibition_id, event_at))
    return cursor.rowcount > 0


def insert_kafka_records_batch(cursor, records, exhibitions, ratings, requests):
    """Insert multiple records from a batch.

    Returns: (inserted_count, duplicate_count)
    """
    inserted = 0
    duplicates = 0

    for record in records:
        was_inserted = insert_kafka_record(
            cursor, record, exhibitions, ratings, requests)
        if was_inserted:
            inserted += 1
        else:
            duplicates += 1

    return inserted, duplicates


def insert_kafka_record(cursor, cleaned_record: dict, exhibitions: dict, ratings: dict, requests: dict) -> bool:
    """
    Insert a cleaned Kafka record into the appropriate table.
    Returns True if inserted, False if duplicate or mapping missing.
    """
    try:
        at = cleaned_record["at"]
        site = cleaned_record["site"]
        val = int(cleaned_record["val"])

        # Get exhibition ID
        exhibition_id = exhibitions.get(f"EXH_{int(site):02d}")
        if exhibition_id is None:
            logger.error(f"Unknown exhibition site {site}")
            return False

        # Route to correct interaction type
        if 0 <= val <= 4:
            # Rating interaction
            rating_id = ratings.get(val)
            if rating_id is None:
                logger.error(f"Unknown rating value {val}")
                return False

            was_inserted = insert_interaction(
                cursor, "rating_interaction", "rating_id", rating_id, exhibition_id, at)
            if was_inserted:
                logger.debug(f"Inserted rating: val={val}, site={site}")
            else:
                logger.debug(f"Duplicate rating: val={val}, site={site}")
            return was_inserted

        elif val == -1:
            # Request interaction
            request_id = requests.get(int(cleaned_record["type"]))
            if request_id is None:
                logger.error(f"Unknown request type {cleaned_record['type']}")
                return False

            was_inserted = insert_interaction(
                cursor, "request_interaction", "request_id", request_id, exhibition_id, at)
            if was_inserted:
                logger.debug(
                    f"Inserted request: type={cleaned_record['type']}, site={site}")
            else:
                logger.debug(
                    f"Duplicate request: type={cleaned_record['type']}, site={site}")
            return was_inserted

    except Exception as e:
        logger.error(f"Error inserting record: {e}")
        return False
