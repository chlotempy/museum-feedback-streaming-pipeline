from __future__ import annotations
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


def is_error_record(record: dict) -> bool:
    """Checks if record is marked as an error."""
    if record.get("type") == "ERR":
        logger.warning(f"Skipping error record: {record}")
        return True
    return False


def has_required_fields(record: dict, required_fields: list[str]) -> bool:
    """Checks if all required fields are present."""
    missing_fields = [f for f in required_fields if f not in record]
    if missing_fields:
        logger.error(f"Missing required fields {missing_fields} in: {record}")
        return False
    logger.debug("All required fields present")
    return True


def is_valid_numeric(value, field_name: str) -> bool:
    """Validates that a value is numeric."""
    try:
        float(value)
        logger.debug(f"{field_name} validated: {value}")
        return True
    except (TypeError, ValueError):
        logger.warning(
            f"Invalid {field_name} type {type(value)} - Record will be skipped")
        return False


def parse_timestamp(timestamp_str: str) -> str | None:
    """Parses and reformats timestamp to standard format."""
    try:
        formatted = datetime.fromisoformat(
            timestamp_str).strftime("%Y-%m-%d %H:%M:%S")
        logger.debug(f"Timestamp converted: {timestamp_str} → {formatted}")
        return formatted
    except ValueError as e:
        logger.error(f"Invalid timestamp format: {timestamp_str} - {e}")
        return None


def is_valid_value_range(value: float) -> bool:
    """Validates that value is between -1 and 4."""
    try:
        val = float(value)
        if -1 <= val <= 4:
            logger.debug(f"Value range validated: {val} is between -1 and 4")
            return True
        else:
            logger.error(f"Value {val} is out of range [-1, 4]")
            return False
    except (TypeError, ValueError):
        logger.error(f"Cannot validate range for non-numeric value: {value}")
        return False


def is_valid_operating_hours(timestamp_str: str) -> bool:
    """Validates that timestamp is within operating hours (8:45am - 6:15pm)."""
    try:
        dt = datetime.fromisoformat(timestamp_str)
        time_obj = dt.time()

        start_time = datetime.strptime("08:45", "%H:%M").time()
        end_time = datetime.strptime("18:15", "%H:%M").time()

        if start_time <= time_obj <= end_time:
            logger.debug(
                f"Time {time_obj} is within operating hours (8:45am - 6:15pm)")
            return True
        else:
            logger.warning(
                f"Time {time_obj} is outside operating hours (8:45am - 6:15pm)")
            return False
    except ValueError as e:
        logger.error(
            f"Invalid timestamp format for operating hours check: {timestamp_str} - {e}")
        return False


def is_valid_button_event(record: dict) -> bool:
    """Validates that record is a valid assistance/emergency button press.

    When val=-1, it indicates a button press event:
    - type: 0 = assistance button
    - type: 1 = emergency button
    """
    if record.get("val") != "-1" and record.get("val") != -1:
        return False

    if "type" not in record:
        logger.error("Button event missing 'type' field")
        return False

    button_type = record.get("type")
    if button_type not in [0, 1]:
        logger.error(
            f"Invalid button type: {button_type}. Must be 0 (assistance) or 1 (emergency)")
        return False

    logger.debug(f"Valid button event: type={button_type}")
    return True


def validate_and_clean_record(json_str: str) -> dict | None:
    """
    Validates and cleans a single Kafka message.

    Handles two types of records:
    1. Rating records: val between -1 and 4 (visitor satisfaction)
    2. Button events: val=-1 with type 0 (assistance) or 1 (emergency)

    Returns cleaned record dict or None if invalid/error.
    """
    import json

    try:
        logger.debug(f"Processing raw message: {json_str}")

        # Parse JSON
        record = json.loads(json_str)
        logger.debug(f"Successfully parsed JSON: {record}")

        # Skip error records
        if is_error_record(record):
            return None

        # Check required fields
        required_fields = ["at", "site", "val"]
        if not has_required_fields(record, required_fields):
            return None

        # Validate value is numeric
        if not is_valid_numeric(record["val"], "Value"):
            return None

        # Validate value is in range [-1, 4]
        if not is_valid_value_range(record["val"]):
            return None

        # Check if this is a button event (val = -1)
        if record.get("val") == "-1" or record.get("val") == -1:
            if not is_valid_button_event(record):
                return None
            logger.debug("Record identified as button event")
        else:
            # Regular rating event - validate site is numeric
            if not is_valid_numeric(record["site"], "Site"):
                return None

        # Validate timestamp is within operating hours
        if not is_valid_operating_hours(record["at"]):
            return None

        # Parse timestamp
        parsed_time = parse_timestamp(record["at"])
        if parsed_time is None:
            return None
        record["at"] = parsed_time

        logger.debug(f"Record successfully cleaned: {record}")
        return record

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON format: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error cleaning record: {e}", exc_info=True)
        return None
