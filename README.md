# LMNH Museum Kiosk Analytics Pipeline

## Project Overview

This is an **ETL (Extract, Transform, Load) pipeline** that processes real-time visitor interaction data from museum kiosks at the Liverpool Natural History Museum (LMNH). The pipeline captures two types of interactions:

1. **Exhibition Ratings**: Visitors can rate exhibitions on a scale of 0-4
2. **Assistance Requests**: Visitors can request assistance from museum staff

### How It Works

The pipeline:
1. **Consumes** raw messages from an Apache Kafka cluster
2. **Validates & Cleans** the data according to business rules (filtering invalid entries, staff interference, mechanical errors)
3. **Enriches** the data with exhibition and rating mappings from a lookup database
4. **Batches** the records (100 records or 10 seconds) to optimize database writes
5. **Inserts** validated interactions into a PostgreSQL database in real-time

The pipeline runs continuously on an AWS EC2 instance, updating the database as kiosk data arrives. A dashboard (Tableau) then visualizes this data to help museum staff make data-driven decisions.

### Data Validation Rules

The pipeline enforces strict data validation based on museum business requirements:

- **Operating Hours**: Only accepts interactions between 8:45 AM and 6:15 PM (LMNH operating hours: 9 AM - 6 PM)
- **Valid Ratings**: Rating values must be 0-4 (rating buttons) or -1 (assistance buttons only)
- **Valid Types**: Message type must be 0 (rating) or 1 (assistance request)
- **Exhibition Filtering**: Only accepts interactions from exhibitions with active kiosks in the system
- **Schema Validation**: All required message keys must be present
- **Duplicate Detection**: Prevents re-inserting identical records

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Museum Kiosks (LMNH)                                   │
│  → Exhibition Rating Buttons (0-4)                      │
│  → Assistance Request Buttons                           │
└────────────────────┬────────────────────────────────────┘
                     │ Real-time data stream
                     ↓
┌─────────────────────────────────────────────────────────┐
│  Apache Kafka (AWS MSK)                                 │
│  Topic: lmnh                                            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│  ETL Pipeline (EC2)                                     │
│  kafka_consumer_pipeline.py                             │
│  → Validate & Clean                                     │
│  → Batch Process                                        │
│  → Duplicate Detection                                  │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL Database (AWS RDS)                          │
│  ├─ rating_interaction                                  │
│  ├─ request_interaction                                 │
│  ├─ exhibition (lookup table)                           │
│  └─ department, floor, rating, request (lookup tables)  │
└─────────────────────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│  Tableau Dashboard                                      │
│  Real-time visualization for museum staff              │
└─────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites

- **Python 3.10+** (macOS, Linux, or Windows with WSL)
- **AWS CLI** (for credential configuration)
- **Terraform** (for production infrastructure provisioning)
- **Access** to LMNH Kafka cluster and database
- A development or production **environment file** (`.env`)

### Step 1: Install System Dependencies

#### macOS
```bash
# Install Terraform (if not already installed)
brew install terraform

# Verify installation
python3 --version    # Should be 3.10+
terraform version    # Should be 1.0+
```

#### Linux (Ubuntu/Debian)
```bash
# Install Terraform
sudo apt-get update
sudo apt-get install -y terraform

# Verify Python is 3.10+
python3 --version
```

### Step 2: Configure AWS CLI

The pipeline uses AWS services (EC2, RDS, MSK). Configure your AWS credentials:

```bash
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: Your AWS access key
- **AWS Secret Access Key**: Your AWS secret key
- **Default region**: eu-west-2 (or your region)
- **Default output format**: json

Or set environment variables:
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_REGION="eu-west-2"
```

### Step 3: Clone and Setup the Project

```bash
# Clone the repository
git clone <repository-url>
cd kiosk_pipeline

# Create a Python virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate  # On macOS/Linux
# OR
.\venv\Scripts\activate   # On Windows

# Install Python dependencies
pip install -r requirements.txt
```

**Important:** Verify that `validator_functions.py` is present in the project root. This file is required for the pipeline to run and should contain the `validate_and_clean_record()` function that validates and cleans kiosk messages according to LMNH business rules.

### Step 4: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and populate all values
# On macOS/Linux:
nano .env

# On Windows:
notepad .env
```

See the [Environment Variables](#environment-variables) section below for detailed guidance.

### Step 5: Verify Database Connection (Local Development Only)

```bash
# Test that the pipeline can connect to the database
python3 -c "from database_functions import connect_to_database; conn = connect_to_database(); print('Database connection successful!'); conn.close()"
```

---

## Environment Variables

Create a `.env` file in the project root (copy from `.env.example`) with the following variables:

### Kafka Configuration

These connect to the Apache Kafka cluster (AWS MSK) that publishes kiosk messages.

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `BOOTSTRAP_SERVERS` | Kafka broker addresses (comma-separated if multiple) | `kafka-broker.example.com:9092` | ✓ Yes |
| `SECURITY_PROTOCOL` | Protocol for Kafka authentication | `SASL_SSL` | ✓ Yes |
| `SASL_MECHANISM` | Kafka SASL authentication method | `PLAIN` | ✓ Yes |
| `USERNAME` | Kafka username for authentication | `kiosk-pipeline-user` | ✓ Yes |
| `PASSWORD` | Kafka password for authentication | `your-secure-password` | ✓ Yes |

### Database Configuration

These connect to the PostgreSQL database (AWS RDS) where validated interactions are stored.

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `DATABASE_IP` | PostgreSQL host address | `lmnh-db.abcd1234.eu-west-2.rds.amazonaws.com` | ✓ Yes |
| `DATABASE_PORT` | PostgreSQL port | `5432` | ✓ Yes |
| `DATABASE_NAME` | Database name | `museum_kiosk_db` | ✓ Yes |
| `DATABASE_USERNAME` | PostgreSQL user | `postgres` | ✓ Yes |
| `DATABASE_PASSWORD` | PostgreSQL password | `your-db-password` | ✓ Yes |

### Environment-Specific Notes

**Local Development:**
- Connect to a shared development database (provided by your team)
- Use Kafka connection details for the development Kafka cluster
- AWS CLI credentials should be configured for other AWS operations

**Production (AWS EC2):**
- Terraform provisions the EC2 instance and RDS database automatically
- The `.env` file on the EC2 instance should use the production database credentials
- See `main.tf` and `terraform.tfvars` for infrastructure configuration

---

## How to Run

### Local Development

Run the pipeline locally for testing and development:

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Start the consumer pipeline
python3 kafka_consumer_pipeline.py
```

The pipeline will:
1. Connect to the Kafka broker
2. Subscribe to the `lmnh` topic
3. Begin consuming messages
4. Validate, clean, and batch-insert records into the database
5. Log activity to both console and `kafka_consumer.log`

**Output Example:**
```
2025-10-09 14:32:10,123 - __main__ - INFO - Kafka Consumer starting up
2025-10-09 14:32:10,456 - __main__ - INFO - Environment variables loaded
2025-10-09 14:32:10,789 - __main__ - INFO - Kafka consumer created successfully
2025-10-09 14:32:10,890 - __main__ - INFO - Subscribed to topic: lmnh
2025-10-09 14:32:15,123 - __main__ - INFO - Batch of 100 records inserted successfully
```

**Stop the pipeline:** Press `Ctrl+C` — the consumer closes gracefully and flushes the final batch.

### Production Deployment (AWS EC2)

The production infrastructure is provisioned using Terraform:

```bash
# From the project root, provision AWS infrastructure
terraform init      # Initialize Terraform
terraform plan      # Review planned changes
terraform apply     # Provision EC2 instance and RDS database
```

This creates:
- An **EC2 instance** (runs the pipeline continuously)
- An **RDS PostgreSQL database** (stores kiosk interactions)
- Security groups (allows EC2 → RDS communication)

Once provisioned:
1. SSH into the EC2 instance
2. Clone this repository
3. Create `.env` with production credentials
4. Run `python3 kafka_consumer_pipeline.py` or set up as a systemd service for auto-restart

See `main.tf` and `terraform.tfvars` for infrastructure details.

---

## Project Structure

| File | Purpose |
|------|---------|
| `kafka_consumer_pipeline.py` | Main entry point. Consumes messages from Kafka, validates, batches, and inserts to database |
| `database_functions.py` | Database operations: connection management, lookups (exhibitions, ratings, requests), batch inserts with duplicate detection |
| `validator_functions.py` | Data validation and cleaning: enforces business rules, filters invalid entries, normalizes timestamps |
| `schema.sql` | SQL schema for PostgreSQL database. Run once during initial setup. Creates lookup tables and interaction tables |
| `reset_database.sh` | Bash script to clear all interaction records while preserving lookup tables (useful for testing) |
| `.env.example` | Template for environment variables. Copy to `.env` and populate with your values |
| `requirements.txt` | Python package dependencies (confluent_kafka, psycopg2-binary, python-dotenv) |
| `main.tf`, `variables.tf`, `terraform.tfvars` | Terraform infrastructure-as-code for AWS provisioning |

---

## Common Tasks

### Resetting Interaction Data

To delete all ratings and requests (while preserving lookup tables), useful for testing:

```bash
./reset_database.sh
```

This clears `rating_interaction` and `request_interaction` tables but keeps exhibition, department, floor, and other reference data intact.

### Reprocessing All Messages

To restart consuming from the beginning of the Kafka topic:

```bash
# In kafka_consumer_pipeline.py, change the group_id to a new value:
# "group_id": "c26-chloe-final-3",  # Previously: "c26-chloe-final-2"
```

Then restart the pipeline. The new `group_id` will read all messages from the beginning.

### Viewing Logs

```bash
# Real-time console output (printed during execution)
# All logs also written to:
tail -f kafka_consumer.log
```

### Running Tests (if available)

```bash
pytest test_validation_functions.py
```

---

## Troubleshooting

### Missing Environment Variables
**Error:** `KeyError: 'BOOTSTRAP_SERVERS'`

**Solution:** Ensure `.env` file exists and contains all required variables. See [Environment Variables](#environment-variables).

### Kafka Connection Refused
**Error:** `KafkaError: _ALL_BROKERS_DOWN`

**Solution:** 
1. Verify `BOOTSTRAP_SERVERS` is correct
2. Check network connectivity to Kafka broker
3. Verify Kafka credentials (USERNAME, PASSWORD, SASL_MECHANISM)

### Database Connection Failed
**Error:** `psycopg2.OperationalError: could not connect to server`

**Solution:**
1. Verify `DATABASE_IP` and `DATABASE_PORT` are correct
2. Check database credentials in `.env`
3. Ensure security group allows EC2 → RDS connection (for production)
4. Test with: `psql -h <DATABASE_IP> -U <DATABASE_USERNAME>`

### Validator Function Not Found
**Error:** `ModuleNotFoundError: No module named 'validator_functions'`

**Cause:** The `validator_functions.py` file is required but missing from the project root.

**Solution:** 
1. Ensure `validator_functions.py` is in the project root directory
2. Verify the file contains the `validate_and_clean_record(decoded_msg: str) -> dict | None` function
3. This function should:
   - Accept a JSON-decoded message string from Kafka
   - Validate against business rules (operating hours, rating ranges, exhibition filtering, etc.)
   - Return a cleaned record dict on success, or `None` if invalid
   - Log any validation errors

---

## Resources

- **Apache Kafka Documentation**: https://kafka.apache.org/documentation/
- **AWS RDS PostgreSQL**: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_PostgreSQL.html
- **Terraform AWS Provider**: https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- **Confluent Kafka Python Client**: https://docs.confluent.io/kafka-clients/python/current/overview.html
- **PostgreSQL Documentation**: https://www.postgresql.org/docs/

---

## Contact & Support

For questions or issues, contact the development team or create an issue in the repository.