# Dashboard

## Running the Kafka Consumer Pipeline

The pipeline (`kafka_consumer_pipeline.py`) consumes museum kiosk messages from the `lmnh` Kafka topic. It validates and cleans each message, then inserts the results into the database in batches. A batch is written when it reaches 100 records or 10 seconds have passed.

### Prerequisites

- Python 3.10+
- A provisioned database (see `main.tf`, or apply `schema.sql` manually)
- Access to the Kafka cluster

### 1. Install dependencies

```bash
cd dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment variables

Create a `.env` file in `dashboard/`:

```
# Kafka
BOOTSTRAP_SERVERS=<kafka bootstrap server>
SECURITY_PROTOCOL=<e.g. SASL_SSL>
SASL_MECHANISM=<e.g. PLAIN>
USERNAME=<kafka username>
PASSWORD=<kafka password>

# Database
DATABASE_IP=<db host>
DATABASE_PORT=<db port>
DATABASE_NAME=<db name>
DATABASE_USERNAME=<db username>
DATABASE_PASSWORD=<db password>
```

Do not commit `.env`.

### 3. Run the pipeline

```bash
python3 kafka_consumer_pipeline.py
```

The consumer subscribes to the `lmnh` topic with `auto.offset.reset=earliest`, so a new `group.id` reads from the start of the topic. Change `group.id` in the script to reprocess all messages. Stop the pipeline with `Ctrl+C`. The consumer closes cleanly and the final batch is flushed.

Logs go to the console and to `kafka_consumer.log`.

### Resetting data

To delete all ratings and requests but keep the lookup tables:

```bash
./reset_database.sh
```

### Running the tests

```bash
pytest test_validation_functions.py
```