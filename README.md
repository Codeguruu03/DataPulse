<div align="center">

# ⚡ DataPulse

### Data Quality-Aware Cloud Data Engineering Platform

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Apache Spark](https://img.shields.io/badge/Apache%20Spark-3.5.0-orange.svg)](https://spark.apache.org/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.8+-teal.svg)](https://airflow.apache.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Terraform](https://img.shields.io/badge/Terraform-AWS%20IaC-7B42BC.svg)](https://www.terraform.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<p align="center">
  <strong>Stop bad data before it silently pollutes analytics dashboards and business decisions.</strong>
</p>

</div>

---

## 📖 Overview

**DataPulse** is a production-grade data engineering platform built to solve the most critical problem in enterprise data pipelines: **Data Trustworthiness**.

Rather than running standard, blind ETL pipelines that propagate bad data downstream, DataPulse enforces **automated data quality gates**, isolates corrupted data into a **quarantine zone with structured audit reasoning**, and produces reliable, partitioned Parquet lakehouse datasets for dimensional warehouse modeling and BI reporting.

### 🌟 Key Highlights

- **Automated Data Quality Gate**: Validates schema contracts, range constraints, duplicate detection, and referential integrity.
- **Smart Quarantine Handling**: Isolates corrupted records instead of failing the entire batch, recording granular error reasons.
- **Dual Storage & Compute Abstraction**:
  - **Local Mode**: 100% free local execution using Docker, PySpark, Parquet, and PostgreSQL.
  - **AWS Cloud Mode**: Provisioned with Terraform to leverage Amazon S3, AWS Glue, Amazon Redshift, and Lambda.
- **Airflow Quality Threshold Gate**: Automatic pipeline circuit-breakers (e.g., if quality score < 95%, halts downstream loads).
- **FastAPI Data Access Layer**: Exposes business analytics metrics and data quality health APIs.
- **Advanced Data Governance**: Data Lineage tracking, Schema Evolution management, and Pipeline Replay backfills.

---

## 🏛️ Architecture

```
                      [ Raw Data Sources ]
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
                 ▼                 [ Error Logs & Metrics ]
        [ Data Warehouse ]                   │
       (PostgreSQL/Redshift)                 │
                 │                           │
                 ├───────────────────────────┘
                 │
        ┌────────┴────────┐
        ▼                 ▼
   [ FastAPI ]      [ Power BI / Analytics ]
(Data Access API)   - Executive Business KPIs
                    - Data Quality Scorecard
```

---

## 📂 Project Structure

```
DataPulse/
├── airflow/                  # Airflow DAGs, plugins & configurations
│   └── dags/                 # Orchestration workflows
├── data/                     # Local data lake tiers (gitignored)
│   ├── raw/                  # Ingested raw datasets
│   ├── processed/            # Partitioned Parquet lakehouse
│   └── quarantine/           # Isolated invalid records & error logs
├── datapulse/                # Core DataPulse Python Engine
│   ├── api/                  # FastAPI serving layer & routes
│   ├── cli/                  # Command line interface commands
│   ├── evolution/            # Schema drift & evolution detection
│   ├── generator/            # Realistic synthetic transaction generator
│   ├── lineage/              # Data lineage tracing engine
│   ├── quality/              # Data quality rules, validator & quarantine
│   ├── replay/               # Pipeline replay & backfill controller
│   ├── schemas/              # Pydantic & PySpark schema contracts
│   ├── storage/              # Pluggable storage abstraction (Local/S3)
│   ├── transforms/           # PySpark transformation jobs
│   ├── utils/                # Logging, metrics, helpers
│   └── warehouse/            # Star schema DDL, loader & analytical marts
├── terraform/                # Infrastructure as Code (AWS S3, Glue, Redshift)
├── tests/                    # Unit, integration, and quality test suite
├── docker-compose.yml        # Multi-service local orchestrator
├── pyproject.toml            # Project dependencies & packaging
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

---

## 🚀 Quickstart

### 1. Setup Environment
```bash
# Clone the repository
git clone https://github.com/Codeguruu03/DataPulse.git
cd DataPulse

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev,spark]"
```

### 2. Check Platform Status
```bash
python -m datapulse.cli info
```

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.
