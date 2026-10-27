import logging

from fastapi import FastAPI, HTTPException

from app.models import ExperimentRequest
from app.services.experiment_runner import run_experiment
from app.settings import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)
logger = logging.getLogger("app.api")
logger.setLevel(logging.DEBUG)


def _format_error_with_cause(exc: Exception) -> tuple[str, str | None, str | None]:
    """Return human-readable error message including chained root cause."""
    error_type = exc.__class__.__name__
    message = str(exc)

    cause = exc.__cause__
    if cause is None:
        return message, error_type, None

    cause_type = cause.__class__.__name__
    cause_message = str(cause)
    composed = f"{message} | cause: {cause_type}: {cause_message}"
    return composed, error_type, cause_type


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/experiment")
def execute_experiment(payload: ExperimentRequest) -> dict:
    logger.debug(
        "Incoming experiment request: experiment_id=%s pipeline=%s llm=%s value=%s approval_links=%d conditions=%d",
        payload.experiment_id,
        payload.pipeline,
        payload.llm.value,
        payload.value,
        len(payload.approval_links),
        len(payload.conditions or []),
    )
    try:
        response = run_experiment(payload)
    except Exception as exc:  # pragma: no cover
        logger.exception(
            "Experiment request failed: experiment_id=%s pipeline=%s llm=%s",
            payload.experiment_id,
            payload.pipeline,
            payload.llm.value,
        )
        error_message, error_type, cause_type = _format_error_with_cause(exc)
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": error_message,
                    "type": error_type,
                    "cause_type": cause_type,
                },
            },
        ) from exc

    logger.debug(
        "Experiment request succeeded: experiment_id=%s pipeline=%s extracted_value=%s",
        payload.experiment_id,
        payload.pipeline,
        response.result.extracted_value,
    )
    return response.model_dump()
