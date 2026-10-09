"""Test suite for validation and cleaning functions."""
from validator_functions import (validate_and_clean_record, is_valid_operating_hours,
                                 is_error_record, has_required_fields, is_valid_numeric,
                                 parse_timestamp, is_valid_value_range, is_valid_button_event)


class TestIsErrorRecord:
    """Test is_error_record function."""

    def test_error_record_with_err_type(self):
        """Should identify records with type ERR."""
        record = {"type": "ERR", "message": "something failed"}
        assert is_error_record(record) is True

    def test_normal_record_not_error(self):
        """Should return False for normal records."""
        record = {"type": "DATA", "value": 10}
        assert is_error_record(record) is False

    def test_missing_type_field(self):
        """Should return False when type field missing."""
        record = {"value": 10}
        assert is_error_record(record) is False


class TestHasRequiredFields:
    """Test has_required_fields function."""

    def test_all_fields_present(self):
        """Should return True when all required fields exist."""
        record = {"at": "2024-10-06T10:30:00", "site": "5", "val": "2.5"}
        required = ["at", "site", "val"]
        assert has_required_fields(record, required) is True

    def test_missing_single_field(self):
        """Should return False when one field is missing."""
        record = {"at": "2024-10-06T10:30:00", "site": "5"}
        required = ["at", "site", "val"]
        assert has_required_fields(record, required) is False

    def test_missing_multiple_fields(self):
        """Should return False when multiple fields are missing."""
        record = {"at": "2024-10-06T10:30:00"}
        required = ["at", "site", "val"]
        assert has_required_fields(record, required) is False

    def test_empty_record(self):
        """Should return False for empty record."""
        record = {}
        required = ["at", "site", "val"]
        assert has_required_fields(record, required) is False


class TestIsValidNumeric:
    """Test is_valid_numeric function."""

    def test_valid_integer(self):
        """Should accept integer values."""
        assert is_valid_numeric(42, "visitor_count") is True

    def test_valid_float(self):
        """Should accept float values."""
        assert is_valid_numeric(3.14, "temperature") is True

    def test_valid_string_number(self):
        """Should accept string representations of numbers."""
        assert is_valid_numeric("42", "humidity") is True
        assert is_valid_numeric("3.14", "pressure") is True

    def test_invalid_string(self):
        """Should reject non-numeric strings."""
        assert is_valid_numeric("malfunction", "sensor_reading") is False

    def test_none_value(self):
        """Should reject None."""
        assert is_valid_numeric(None, "air_quality") is False

    def test_negative_numbers(self):
        """Should accept negative numbers."""
        assert is_valid_numeric(-5.5, "pressure") is True


class TestParseTimestamp:
    """Test parse_timestamp function."""

    def test_valid_iso_format(self):
        """Should parse valid ISO format timestamp."""
        result = parse_timestamp("2024-10-06T10:30:45")
        assert result == "2024-10-06 10:30:45"

    def test_valid_iso_with_microseconds(self):
        """Should parse ISO format with microseconds."""
        result = parse_timestamp("2024-10-06T10:30:45.123456")
        assert result == "2024-10-06 10:30:45"

    def test_invalid_format(self):
        """Should return None for invalid format."""
        result = parse_timestamp("10/06/2024")
        assert result is None

    def test_malformed_timestamp(self):
        """Should return None for malformed timestamps."""
        result = parse_timestamp("not-a-timestamp")
        assert result is None

    def test_empty_string(self):
        """Should return None for empty string."""
        result = parse_timestamp("")
        assert result is None


class TestIsValidValueRange:
    """Test is_valid_value_range function."""

    def test_value_at_lower_bound(self):
        """Should accept value at -1."""
        assert is_valid_value_range(-1) is True

    def test_value_at_upper_bound(self):
        """Should accept value at 4."""
        assert is_valid_value_range(4) is True

    def test_value_in_range(self):
        """Should accept values between -1 and 4."""
        assert is_valid_value_range(0) is True
        assert is_valid_value_range(2.5) is True
        assert is_valid_value_range(3.99) is True

    def test_value_below_range(self):
        """Should reject values below -1."""
        assert is_valid_value_range(-1.1) is False
        assert is_valid_value_range(-5) is False

    def test_value_above_range(self):
        """Should reject values above 4."""
        assert is_valid_value_range(4.1) is False
        assert is_valid_value_range(10) is False

    def test_string_value_in_range(self):
        """Should accept string representations within range."""
        assert is_valid_value_range("2") is True

    def test_invalid_string_value(self):
        """Should reject non-numeric strings."""
        assert is_valid_value_range("not-a-number") is False


class TestIsValidOperatingHours:
    """Test is_valid_operating_hours function."""

    def test_within_operating_hours_morning(self):
        """Should accept timestamps during operating hours (morning)."""
        assert is_valid_operating_hours("2024-10-06T09:00:00") is True

    def test_within_operating_hours_afternoon(self):
        """Should accept timestamps during operating hours (afternoon)."""
        assert is_valid_operating_hours("2024-10-06T15:30:00") is True

    def test_at_start_time(self):
        """Should accept timestamp at 8:25am."""
        assert is_valid_operating_hours("2024-10-06T08:25:00") is True

    def test_at_end_time(self):
        """Should accept timestamp at 6:15pm."""
        assert is_valid_operating_hours("2024-10-06T18:15:00") is True

    def test_before_operating_hours(self):
        """Should reject timestamps before 8:25am."""
        assert is_valid_operating_hours("2024-10-06T08:24:00") is False
        assert is_valid_operating_hours("2024-10-06T06:00:00") is False

    def test_after_operating_hours(self):
        """Should reject timestamps after 6:15pm."""
        assert is_valid_operating_hours("2024-10-06T18:16:00") is False
        assert is_valid_operating_hours("2024-10-06T22:00:00") is False

    def test_invalid_timestamp_format(self):
        """Should return False for invalid timestamp format."""
        assert is_valid_operating_hours("not-a-timestamp") is False


class TestIsValidButtonEvent:
    """Test is_valid_button_event function."""

    def test_valid_assistance_button_event(self):
        """Should accept valid assistance button press (type=0)."""
        record = {"val": "-1", "type": 0}
        assert is_valid_button_event(record) is True

    def test_valid_emergency_button_event(self):
        """Should accept valid emergency button press (type=1)."""
        record = {"val": "-1", "type": 1}
        assert is_valid_button_event(record) is True

    def test_valid_button_event_with_int_val(self):
        """Should accept button event with integer val=-1."""
        record = {"val": -1, "type": 0}
        assert is_valid_button_event(record) is True

    def test_button_event_missing_type_field(self):
        """Should reject button event missing type field."""
        record = {"val": "-1"}
        assert is_valid_button_event(record) is False

    def test_button_event_invalid_type_value(self):
        """Should reject button event with invalid type (not 0 or 1)."""
        record = {"val": "-1", "type": 2}
        assert is_valid_button_event(record) is False

    def test_button_event_with_negative_type(self):
        """Should reject button event with negative type."""
        record = {"val": "-1", "type": -1}
        assert is_valid_button_event(record) is False

    def test_not_button_event_with_valid_rating(self):
        """Should reject record with valid rating val (not -1)."""
        record = {"val": "2", "type": 0}
        assert is_valid_button_event(record) is False

    def test_button_event_with_wrong_val_type(self):
        """Should reject if val is not -1."""
        record = {"val": "0", "type": 0}
        assert is_valid_button_event(record) is False


class TestValidateAndCleanRecord:
    """Test validate_and_clean_record function."""

    # === Rating Event Tests ===
    def test_valid_rating_record(self):
        """Should clean and return valid rating record."""
        json_str = '{"at": "2024-10-06T10:30:00", "site": "5", "val": "2.5"}'
        result = validate_and_clean_record(json_str)
        assert result is not None
        assert result["at"] == "2024-10-06 10:30:00"
        assert result["site"] == "5"
        assert result["val"] == "2.5"

    def test_valid_positive_rating(self):
        """Should accept positive visitor satisfaction rating."""
        json_str = '{"at": "2024-10-06T14:00:00", "site": "bugs", "val": "3"}'
        result = validate_and_clean_record(json_str)
        assert result is not None
        assert result["val"] == "3"

    def test_valid_neutral_rating(self):
        """Should accept neutral visitor rating."""
        json_str = '{"at": "2024-10-06T11:30:00", "site": "dino", "val": "0"}'
        result = validate_and_clean_record(json_str)
        assert result is not None
        assert result["val"] == "0"

    def test_valid_max_rating(self):
        """Should accept maximum visitor satisfaction rating."""
        json_str = '{"at": "2024-10-06T15:45:00", "site": "whales", "val": "4"}'
        result = validate_and_clean_record(json_str)
        assert result is not None
        assert result["val"] == "4"

    def test_error_record_rejected(self):
        """Should reject records with type ERR."""
        json_str = '{"type": "ERR", "at": "2024-10-06T10:30:00", "site": "5", "val": "2.5"}'
        result = validate_and_clean_record(json_str)
        assert result is None

    def test_missing_required_field(self):
        """Should reject records missing required fields."""
        json_str = '{"at": "2024-10-06T10:30:00", "site": "5"}'
        result = validate_and_clean_record(json_str)
        assert result is None

    def test_invalid_json(self):
        """Should reject invalid JSON."""
        json_str = 'not valid json'
        result = validate_and_clean_record(json_str)
        assert result is None

    def test_non_numeric_value(self):
        """Should reject non-numeric rating values."""
        json_str = '{"at": "2024-10-06T10:30:00", "site": "5", "val": "abc"}'
        result = validate_and_clean_record(json_str)
        assert result is None

    def test_value_out_of_range(self):
        """Should reject rating values outside [-1, 4]."""
        json_str = '{"at": "2024-10-06T10:30:00", "site": "5", "val": "5"}'
        result = validate_and_clean_record(json_str)
        assert result is None

    def test_non_numeric_site(self):
        """Should reject non-numeric site values."""
        json_str = '{"at": "2024-10-06T10:30:00", "site": "invalid", "val": "2.5"}'
        result = validate_and_clean_record(json_str)
        assert result is None

    def test_outside_operating_hours(self):
        """Should reject timestamps outside operating hours."""
        json_str = '{"at": "2024-10-06T22:00:00", "site": "5", "val": "2.5"}'
        result = validate_and_clean_record(json_str)
        assert result is None

    # === Button Event Tests ===
    def test_valid_assistance_button_event(self):
        """Should accept valid assistance button press (type=0)."""
        json_str = '{"at": "2024-10-06T10:30:00", "site": "bugs", "val": "-1", "type": 0}'
        result = validate_and_clean_record(json_str)
        assert result is not None
        assert result["val"] == "-1"
        assert result["type"] == 0

    def test_valid_emergency_button_event(self):
        """Should accept valid emergency button press (type=1)."""
        json_str = '{"at": "2024-10-06T12:45:00", "site": "dino", "val": "-1", "type": 1}'
        result = validate_and_clean_record(json_str)
        assert result is not None
        assert result["val"] == "-1"
        assert result["type"] == 1

    def test_button_event_missing_type_field(self):
        """Should reject button event (val=-1) missing type field."""
        json_str = '{"at": "2024-10-06T10:30:00", "site": "cave", "val": "-1"}'
        result = validate_and_clean_record(json_str)
        assert result is None

    def test_button_event_invalid_type(self):
        """Should reject button event with invalid type (not 0 or 1)."""
        json_str = '{"at": "2024-10-06T10:30:00", "site": "pollution", "val": "-1", "type": 2}'
        result = validate_and_clean_record(json_str)
        assert result is None

    def test_button_event_outside_operating_hours(self):
        """Should reject button event recorded outside operating hours."""
        json_str = '{"at": "2024-10-06T07:00:00", "site": "explorer", "val": "-1", "type": 0}'
        result = validate_and_clean_record(json_str)
        assert result is None

    def test_button_event_at_opening_time(self):
        """Should accept button event at museum opening time."""
        json_str = '{"at": "2024-10-06T08:25:00", "site": "bugs", "val": "-1", "type": 1}'
        result = validate_and_clean_record(json_str)
        assert result is not None

    def test_button_event_at_closing_time(self):
        """Should accept button event at museum closing time."""
        json_str = '{"at": "2024-10-06T18:15:00", "site": "whales", "val": "-1", "type": 0}'
        result = validate_and_clean_record(json_str)
        assert result is not None

    # === Mixed/Edge Case Tests ===
    def test_rating_with_button_type_field(self):
        """Should accept rating (val != -1) even if type field is present."""
        json_str = '{"at": "2024-10-06T10:30:00", "site": "bugs", "val": "2", "type": 0}'
        result = validate_and_clean_record(json_str)
        assert result is not None
        assert result["val"] == "2"
