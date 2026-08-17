<div align="center">

# ⚡ DataPulse

### Data Quality-Aware Cloud Data Engineering Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5.0-orange.svg)](https://spark.apache.org/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.8+-teal.svg)](https://airflow.apache.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Terraform](https://img.shields.io/badge/Terraform-AWS%20IaC-7B42BC.svg)](https://www.terraform.io/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://www.docker.com/)
[![CI](https://github.com/Codeguruu03/DataPulse/actions/workflows/ci.yml/badge.svg)](https://github.com/Codeguruu03/DataPulse/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <strong>Guarantees that low-quality, corrupt, or invalid business data never silently pollutes analytics systems.</strong>
</p>

</div>

---

## 📖 Overview

**DataPulse** is a production-grade data engineering platform built to solve the most critical problem in enterprise data architectures: **Data Trustworthiness**.

Rather than running blind ETL pipelines that blindly copy bad data into downstream systems, DataPulse enforces **automated data quality gates**, isolates corrupted records into a **quarantine zone with structured audit reasoning**, and produces reliable, partitioned Parquet lakehouse datasets for Star Schema warehouse dimensional modeling and BI reporting.

---

## 🏛️ Architecture & End-to-End Flow

```
                      [ RAW DATA SOURCES ]
                   (orders, customers, products)
                               │
                               ▼
                    [ Ingestion Layer (Python) ]
                               │
                               ▼
                       [ Raw Zone Storage ]
                               │
                               ▼
                 [ Processing Layer (PySpark) ]
                               │
                               ▼
                     ┌───────────────────┐
                     │ Data Quality Gate │
                     └─────────┬─────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
          [ VALID DATA ]              [ INVALID DATA ]
                 │                           │
                 ▼                           ▼
        [ Processed Parquet ]          [ Quarantine Zone ]
     (partitioned: year/month)               │
                 │                           ▼
                 ▼                 [ Error Logs & Audit JSON ]
        [ Data Warehouse ]                   │
       (PostgreSQL/Redshift)                 │
                 │                           │
                 ├───────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   [ FastAPI ]      [ Power BI / Web Dashboard ]
(Data Access API)   - Executive Business KPIs
                    - Data Quality Scorecard
                    - Quarantine Inspector
```

---

## 🌟 Key Features

| Capability | Enterprise Value |
|---|---|
| **Automated Data Quality Gate** | Multi-point vectorized validations (uniqueness, null checks, numeric bounds, date formats, referential integrity). |
| **Quarantine Routing** | Corrupted records are isolated with detailed error reasons without crashing or contaminating clean datasets. |
| **Circuit-Breaker Orchestration** | Airflow DAG short-circuits downstream loads if quality falls below a configurable threshold (e.g. `< 95%`). |
| **Lakehouse Partitioned Parquet** | Optimized columnar storage partitioned by `year=YYYY/month=MM` for fast analytical querying. |
| **Star Schema Data Warehouse** | Dimensional model with `fact_orders`, `dim_customers`, `dim_products`, `dim_date`, and pre-aggregated Mart views. |
| **FastAPI Serving & Live UI** | REST API exposing business analytics, quality health metrics, and an interactive dark-mode dashboard with Chart.js. |
| **Data Lineage Tracker** | Traces any dashboard KPI or warehouse table upstream to its exact source file and transformation steps. |
| **Schema Evolution Engine** | Detects schema drift (compatible extensions vs breaking column removals). |
| **Pipeline Replay Engine** | Re-executes pipeline runs from validation checkpoints without re-fetching raw data dumps. |
| **Cloud Portability (Local / AWS)** | 100% free local execution (Docker/Postgres/Spark) with complete Terraform IaC for AWS deployment (S3/Glue/Redshift). |

---

## 📂 Project Structure

```
DataPulse/
├── .github/workflows/        # GitHub Actions CI/CD pipeline
├── airflow/                  # Airflow DAGs & orchestration
│   └── dags/                 # datapulse_daily_etl_dag.py
├── data/                     # Local data lake tiers (gitignored)
│   ├── raw/                  # Ingested raw datasets
│   ├── processed/            # Partitioned Parquet lakehouse
│   └── quarantine/           # Isolated invalid records & error logs
├── datapulse/                # Core DataPulse Python Engine
│   ├── api/                  # FastAPI serving layer & routes
│   │   ├── routes/           # analytics, quality, pipeline endpoints
│   │   └── static/           # Modern Glassmorphic Web Dashboard UI
│   ├── cli/                  # Click CLI command suite
│   ├── evolution/            # Schema drift & evolution detector
│   ├── generator/            # Realistic synthetic transaction generator
│   ├── lineage/              # Data lineage graph & Mermaid generator
│   ├── orchestration/        # Pipeline runner & circuit breaker
│   ├── quality/              # Data quality rules, validator & quarantine
│   ├── replay/               # Pipeline replay controller
│   ├── schemas/              # Pydantic & dimensional models
│   ├── storage/              # Pluggable storage abstraction (Local/S3)
│   ├── transforms/           # Cleaners, enrichment & Parquet pipeline
│   └── warehouse/            # Star schema DDL, loader & analytical marts
├── terraform/                # Infrastructure as Code (AWS S3, Glue, Redshift, IAM)
├── tests/                    # 23+ Unit, integration, and quality tests
├── docker-compose.yml        # Multi-service local stack (Postgres, Airflow, API)
├── Dockerfile                # Production container definition
├── pyproject.toml            # Build configurations
└── requirements.txt          # Python dependencies
```

---

## 🚀 Quickstart Guide

### 1. Installation
```bash
# Clone the repository
git clone https://github.com/Codeguruu03/DataPulse.git
cd DataPulse

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
```

### 2. Run End-to-End Pipeline
```bash
# Run the complete orchestrated pipeline with quality gates
python -m datapulse.cli.main pipeline run --threshold 95.0 --anomaly-rate 0.05
```

### 3. Start Interactive Dashboard & API
```bash
python -m datapulse.cli.main serve --port 8000
```
- Open **Dashboard UI**: [http://localhost:8000/dashboard/index.html](http://localhost:8000/dashboard/index.html)
- Open **Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 💻 CLI Command Reference

```bash
# Generate synthetic enterprise data with noise
datapulse generate --orders 5000 --customers 500 --anomaly-rate 0.05

# Evaluate data quality gate & quarantine corrupted records
datapulse validate --threshold 95.0

# Transform clean datasets into partitioned Parquet Lakehouse
datapulse transform

# Initialize and load Star Schema Warehouse
datapulse warehouse init
datapulse warehouse load
datapulse warehouse mart monthly_revenue

# Trace data lineage upstream
datapulse lineage --target v_mart_monthly_revenue

# Check for schema drift
datapulse evolution --dataset orders

# Replay pipeline from validation checkpoint
datapulse replay --run-id <RUN_ID> --threshold 90.0
```

---

## 🐳 Docker Compose Stack

Run PostgreSQL, Airflow, and FastAPI in a single command:
```bash
docker compose up -d
```
- **FastAPI & Dashboard**: `http://localhost:8000`
- **Airflow Webserver**: `http://localhost:8080` (admin / admin)
- **PostgreSQL Warehouse**: `localhost:5432`

---

## ☁️ AWS Cloud Deployment (Terraform)

Deploy S3 Data Lake, AWS Glue, and Amazon Redshift:
```bash
cd terraform
terraform init
terraform plan
terraform apply
```

---

## 🧪 Testing

Run the full automated test suite (23 test cases):
```bash
pytest -v
```

---

## 💼 Interview Talking Points

> **Q: "What problem did your project solve?"**
> 
> *"DataPulse ensures that business data is trustworthy before it reaches analytics. It automatically detects data-quality and schema problems, quarantines invalid data with detailed reasoning, stops bad pipeline runs using automated circuit breakers, and produces validated, partitioned Parquet lakehouse datasets for analytics."*

---

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
