"""
Pipeline Execution and Trigger API Endpoints.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel, Field

from datapulse.orchestration.runner import PipelineRunner
from datapulse.config import settings

router = APIRouter(prefix="/pipeline", tags=["Pipeline Execution"])

# Cache latest run result in memory
LATEST_PIPELINE_RUN: Dict[str, Any] = {
    "status": "IDLE",
    "message": "Ready to execute pipeline",
}


class PipelineTriggerRequest(BaseModel):
    threshold: Optional[float] = Field(default=95.0, description="Quality gate pass threshold %")
    anomaly_rate: Optional[float] = Field(default=0.05, description="Synthetic noise rate")
    auto_generate: Optional[bool] = Field(default=True, description="Generate new synthetic data")


def _execute_pipeline_task(req: PipelineTriggerRequest):
    global LATEST_PIPELINE_RUN
    runner = PipelineRunner(
        quality_threshold=req.threshold,
        auto_generate=req.auto_generate,
        anomaly_rate=req.anomaly_rate,
    )
    result = runner.run()
    LATEST_PIPELINE_RUN = result


@router.post("/trigger")
def trigger_pipeline(
    req: PipelineTriggerRequest,
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """Triggers an end-to-end DataPulse pipeline execution."""
    global LATEST_PIPELINE_RUN
    LATEST_PIPELINE_RUN = {
        "status": "RUNNING",
        "message": "Pipeline execution triggered in background",
        "threshold": req.threshold,
    }
    background_tasks.add_task(_execute_pipeline_task, req)
    return {
        "status": "ACCEPTED",
        "message": "Pipeline run queued successfully",
        "config": req.model_dump(),
    }


@router.get("/status")
def get_pipeline_status() -> Dict[str, Any]:
    """Retrieves the status and stage logs of the most recent pipeline execution."""
    global LATEST_PIPELINE_RUN
    return LATEST_PIPELINE_RUN
