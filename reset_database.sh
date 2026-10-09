#!/bin/bash

# Database Reset Script
# Removes all interaction data (ratings and requests) while preserving
# table structures and lookup data (exhibitions, departments, etc.)

set -e  # Exit on error

# Load environment variables
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    exit 1
fi

source .env

# Extract database credentials
DB_HOST="${DATABASE_IP}"
DB_PORT="${DATABASE_PORT}"
DB_NAME="${DATABASE_NAME}"
DB_USER="${DATABASE_USERNAME}"
DB_PASSWORD="${DATABASE_PASSWORD}"

echo "=========================================="
echo "Database Reset Script"
echo "=========================================="
echo "Database: $DB_NAME"
echo "Host: $DB_HOST:$DB_PORT"
echo ""

# Confirm before proceeding
read -p "This will delete ALL interaction data. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Execute reset via psql
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_NAME" \
    << EOF

-- Delete all interaction records
DELETE FROM rating_interaction;
DELETE FROM request_interaction;

-- Reset auto-increment counters
ALTER SEQUENCE rating_interaction_rating_interaction_id_seq RESTART WITH 1;
ALTER SEQUENCE request_interaction_request_interaction_id_seq RESTART WITH 1;

-- Verify tables are empty
SELECT 'rating_interaction' as table_name, COUNT(*) as row_count FROM rating_interaction
UNION ALL
SELECT 'request_interaction', COUNT(*) FROM request_interaction;

EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ Database reset successful!"
    echo "  - All interaction data deleted"
    echo "  - Tables and lookup data preserved"
else
    echo ""
    echo "✗ Database reset failed!"
    exit 1
fi