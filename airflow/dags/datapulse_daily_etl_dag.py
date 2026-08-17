"""
Airflow Production DAG: DataPulse Daily Enterprise ETL & Quality Gate Pipeline.

Orchestrates multi-source ingestion, strict automated quality gate verification,
conditional circuit-breaking threshold enforcement, PySpark lakehouse transformations,
and Star Schema analytical warehouse loading.
"""

from datetime import datetime, timedelta
import os
import sys

# Ensure datapulse is on pythonpath for Airflow workers
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator, ShortCircuitOperator
    from airflow.operators.empty import EmptyOperator
except ImportError:
    # Allows DAG file to be parsed or imported in non-Airflow test environments
    DAG = None
    PythonOperator = None
    ShortCircuitOperator = None
    EmptyOperator = None


def run_ingestion(**context):
    """Task 1: Ingests raw data files or runs synthetic generator."""
    from datapulse.generator.generator import DataPulseGenerator
    from datapulse.config import settings
    
    gen = DataPulseGenerator(anomaly_rate=0.05)
    c, p, o = gen.generate_all_and_save()
    context["ti"].xcom_push(key="raw_files", value={"customers": str(c), "products": str(p), "orders": str(o)})
    return "Ingestion complete"


def run_quality_gate(**context):
    """Task 2: Executes automated Data Quality Gate and quarantines invalid records."""
    from datapulse.quality.gate import DataQualityGate
    
    gate = DataQualityGate()
    passed, summary, datasets = gate.evaluate_pipeline_batch()
    
    # Push quality metrics to Airflow XCom
    context["ti"].xcom_push(key="quality_score", value=summary.overall_quality_score)
    context["ti"].xcom_push(key="quality_passed", value=passed)
    context["ti"].xcom_push(key="run_id", value=summary.run_id)
    
    return summary.model_dump(mode="json")


def quality_threshold_circuit_breaker(**context):
    """
    Task 3: ShortCircuitOperator logic.
    Halts all downstream tasks if data quality score is below threshold (default: 95%).
    """
    ti = context["ti"]
    passed = ti.xcom_pull(key="quality_passed", task_ids="quality_gate_evaluation")
    score = ti.xcom_pull(key="quality_score", task_ids="quality_gate_evaluation")
    
    if not passed:
        print(f"[CIRCUIT BREAKER TRIGGERED] Quality score ({score}%) below threshold. Stopping downstream ETL.")
        return False
    print(f"[QUALITY GATE PASSED] Quality score ({score}%) meets criteria. Proceeding with Lakehouse transformations.")
    return True


def run_spark_lakehouse_transform(**context):
    """Task 4: PySpark lakehouse transformation and Parquet partitioning."""
    from datapulse.quality.gate import DataQualityGate
    from datapulse.transforms.pipeline import LakehouseTransformPipeline
    
    ti = context["ti"]
    run_id = ti.xcom_pull(key="run_id", task_ids="quality_gate_evaluation")
    
    gate = DataQualityGate()
    _, _, valid_datasets = gate.evaluate_pipeline_batch(run_id=run_id)
    
    pipeline = LakehouseTransformPipeline()
    manifest = pipeline.process_and_publish_lake(valid_datasets, run_id=run_id)
    return manifest


def run_warehouse_load(**context):
    """Task 5: Loads Parquet datasets into Star Schema warehouse."""
    from datapulse.warehouse.loader import WarehouseLoader
    
    loader = WarehouseLoader()
    stats = loader.load_lakehouse_to_warehouse()
    return stats


default_args = {
    "owner": "datapulse",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "start_date": datetime(2026, 1, 1),
}

if DAG:
    dag = DAG(
        "datapulse_daily_etl_dag",
        default_args=default_args,
        description="Data Quality-Aware End-to-End Enterprise Data Pipeline",
        schedule_interval="0 2 * * *",  # Daily at 02:00 AM UTC
        catchup=False,
        tags=["datapulse", "quality-gate", "pyspark", "warehouse"],
    )

    with dag:
        start_task = EmptyOperator(task_id="start_pipeline")

        ingest_task = PythonOperator(
            task_id="ingest_raw_data",
            python_callable=run_ingestion,
            provide_context=True,
        )

        quality_gate_task = PythonOperator(
            task_id="quality_gate_evaluation",
            python_callable=run_quality_gate,
            provide_context=True,
        )

        circuit_breaker_task = ShortCircuitOperator(
            task_id="quality_threshold_circuit_breaker",
            python_callable=quality_threshold_circuit_breaker,
            provide_context=True,
        )

        transform_task = PythonOperator(
            task_id="pyspark_lakehouse_transform",
            python_callable=run_spark_lakehouse_transform,
            provide_context=True,
        )

        warehouse_task = PythonOperator(
            task_id="load_star_schema_warehouse",
            python_callable=run_warehouse_load,
            provide_context=True,
        )

        end_task = EmptyOperator(task_id="pipeline_complete")

        # Define Task Dependency Graph
        start_task >> ingest_task >> quality_gate_task >> circuit_breaker_task >> transform_task >> warehouse_task >> end_task
