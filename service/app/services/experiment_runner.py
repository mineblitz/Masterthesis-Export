import logging

from app.models import ExperimentRequest, ExperimentResponse
from app.services.pipelines.text_only_simple_conversion import run_text_only_simple_conversion
from app.services.pipelines.text_only_simple_conversion_v2 import run_text_only_simple_conversion_v2
from app.services.pipelines.text_only_simple_conversion_v3 import run_text_only_simple_conversion_v3
from app.services.pipelines.text_only_simple_conversion_v4 import run_text_only_simple_conversion_v4
from app.services.pipelines.text_only_simple_conversion_v5 import run_text_only_simple_conversion_v5
from app.services.pipelines.text_only_simple_conversion_v6 import run_text_only_simple_conversion_v6
from app.services.pipelines.text_only_simple_conversion_v7 import run_text_only_simple_conversion_v7
from app.services.pipelines.text_only_simple_conversion_v8 import run_text_only_simple_conversion_v8
from app.services.pipelines.text_only_simple_conversion_v9 import run_text_only_simple_conversion_v9
from app.services.pipelines.text_only_simple_conversion_v10 import run_text_only_simple_conversion_v10
from app.services.pipelines.text_only_simple_conversion_v15 import run_text_only_simple_conversion_v15
from app.services.pipelines.text_only_simple_conversion_v16 import run_text_only_simple_conversion_v16
from app.services.pipelines.text_only_simple_conversion_v17 import run_text_only_simple_conversion_v17
from app.services.pipelines.text_only_simple_conversion_v18 import run_text_only_simple_conversion_v18
from app.services.pipelines.text_only_simple_conversion_v20 import run_text_only_simple_conversion_v20
from app.services.pipelines.text_only_simple_conversion_v21 import run_text_only_simple_conversion_v21
from app.services.pipelines.text_only_simple_conversion_v22 import run_text_only_simple_conversion_v22
from app.services.pipelines.text_only_simple_conversion_v23 import run_text_only_simple_conversion_v23
from app.services.pipelines.text_only_simple_conversion_v24 import run_text_only_simple_conversion_v24
from app.services.pipelines.text_only_simple_conversion_v25 import run_text_only_simple_conversion_v25
from app.services.pipelines.text_only_simple_conversion_v26 import run_text_only_simple_conversion_v26
from app.services.pipelines.text_only_simple_conversion_v27 import run_text_only_simple_conversion_v27
from app.services.pipelines.text_only_simple_conversion_v28 import run_text_only_simple_conversion_v28
from app.services.pipelines.text_only_simple_conversion_v29 import run_text_only_simple_conversion_v29
from app.services.pipelines.text_only_simple_conversion_v30 import run_text_only_simple_conversion_v30
from app.services.pipelines.text_only_simple_conversion_v31 import run_text_only_simple_conversion_v31
from app.services.pipelines.text_only_simple_conversion_v32 import run_text_only_simple_conversion_v32
from app.services.pipelines.text_only_simple_conversion_v33 import run_text_only_simple_conversion_v33
from app.services.pipelines.text_only_simple_conversion_v34 import run_text_only_simple_conversion_v34
from app.services.pipelines.text_only_simple_conversion_v35 import run_text_only_simple_conversion_v35
from app.services.pipelines.text_only_simple_conversion_v36 import run_text_only_simple_conversion_v36
from app.services.pipelines.direct_qa_v1 import run_direct_qa_v1
from app.services.pipelines.direct_qa_conditional_chunk_v1 import (
    run_direct_qa_conditional_chunk_v1,
)
from app.services.pipelines.kg_comprehensive_schema_minimal_turtle_v4 import run_kg_comprehensive_schema_minimal_turtle_v4
from app.services.pipelines.text_image_multimodal_conversion_v23 import run_text_image_multimodal_conversion_v23
from app.services.pipelines.kg_turtle_extraction_cable_v1 import run_kg_turtle_extraction_cable_v1
from app.services.pipelines.kg_turtle_extraction_pipe_v1 import run_kg_turtle_extraction_pipe_v1
from app.services.pipelines.kg_comprehensive_schema_minimal_turtle_v1 import (
    run_kg_comprehensive_schema_minimal_turtle_v1,
)
from app.services.pipelines.kg_comprehensive_schema_minimal_turtle_v2 import (
    run_kg_comprehensive_schema_minimal_turtle_v2,
)
from app.services.pipelines.kg_comprehensive_schema_minimal_turtle_v3 import (
    run_kg_comprehensive_schema_minimal_turtle_v3,
)
from app.services.pipelines.text_image_multimodal_conversion_v11 import (
    run_text_image_multimodal_conversion_v11,
)
from app.services.pipelines.text_image_multimodal_conversion_v19 import (
    run_text_image_multimodal_conversion_v19,
)
from app.services.pipelines.text_image_multimodal_conversion_v21 import (
    run_text_image_multimodal_conversion_v21,
)
from app.services.pipelines.text_image_multimodal_conversion_v22 import (
    run_text_image_multimodal_conversion_v22,
)
from app.services.pipelines.turtle_kg_conversion_v12 import run_turtle_kg_conversion_v12
from app.services.pipelines.turtle_kg_keyword_v14 import run_turtle_kg_keyword_v14
from app.services.pipelines.turtle_kg_keyword_v15 import run_turtle_kg_keyword_v15
from app.services.pipelines.turtle_kg_twostep_v13 import run_turtle_kg_twostep_v13


logger = logging.getLogger("app.experiment_runner")
logger.setLevel(logging.DEBUG)


def _normalize_pipeline_name(pipeline: str) -> str:
    if pipeline.startswith("run_"):
        return pipeline.removeprefix("run_")
    return pipeline


def run_experiment(payload: ExperimentRequest) -> ExperimentResponse:
    """Run a single experiment request using the configured pipeline."""
    pipeline_name = _normalize_pipeline_name(payload.pipeline)
    logger.debug(
        "Dispatching experiment: experiment_id=%s pipeline=%s normalized_pipeline=%s",
        payload.experiment_id,
        payload.pipeline,
        pipeline_name,
    )

    if pipeline_name == "text_only_simple_conversion":
        return run_text_only_simple_conversion(payload)
    if pipeline_name == "text_only_simple_conversion_v2":
        return run_text_only_simple_conversion_v2(payload)
    if pipeline_name == "text_only_simple_conversion_v3":
        return run_text_only_simple_conversion_v3(payload)
    if pipeline_name == "text_only_simple_conversion_v4":
        return run_text_only_simple_conversion_v4(payload)
    if pipeline_name == "text_only_simple_conversion_v5":
        return run_text_only_simple_conversion_v5(payload)
    if pipeline_name == "text_only_simple_conversion_v6":
        return run_text_only_simple_conversion_v6(payload)
    if pipeline_name == "text_only_simple_conversion_v7":
        return run_text_only_simple_conversion_v7(payload)
    if pipeline_name == "text_only_simple_conversion_v8":
        return run_text_only_simple_conversion_v8(payload)
    if pipeline_name == "text_only_simple_conversion_v9":
        return run_text_only_simple_conversion_v9(payload)
    if pipeline_name == "text_only_simple_conversion_v10":
        return run_text_only_simple_conversion_v10(payload)
    if pipeline_name == "text_only_simple_conversion_v15":
        return run_text_only_simple_conversion_v15(payload)
    if pipeline_name == "text_only_simple_conversion_v16":
        return run_text_only_simple_conversion_v16(payload)
    if pipeline_name == "text_only_simple_conversion_v17":
        return run_text_only_simple_conversion_v17(payload)
    if pipeline_name == "text_only_simple_conversion_v18":
        return run_text_only_simple_conversion_v18(payload)
    if pipeline_name == "text_only_simple_conversion_v20":
        return run_text_only_simple_conversion_v20(payload)
    if pipeline_name == "text_only_simple_conversion_v21":
        return run_text_only_simple_conversion_v21(payload)
    if pipeline_name == "text_only_simple_conversion_v22":
        return run_text_only_simple_conversion_v22(payload)
    if pipeline_name == "text_only_simple_conversion_v23":
        return run_text_only_simple_conversion_v23(payload)
    if pipeline_name == "text_only_simple_conversion_v24":
        return run_text_only_simple_conversion_v24(payload)
    if pipeline_name == "text_only_simple_conversion_v25":
        return run_text_only_simple_conversion_v25(payload)
    if pipeline_name == "text_only_simple_conversion_v26":
        return run_text_only_simple_conversion_v26(payload)
    if pipeline_name == "text_only_simple_conversion_v27":
        return run_text_only_simple_conversion_v27(payload)
    if pipeline_name == "text_only_simple_conversion_v28":
        return run_text_only_simple_conversion_v28(payload)
    if pipeline_name == "text_only_simple_conversion_v29":
        return run_text_only_simple_conversion_v29(payload)
    if pipeline_name == "text_only_simple_conversion_v30":
        return run_text_only_simple_conversion_v30(payload)
    if pipeline_name == "text_only_simple_conversion_v31":
        return run_text_only_simple_conversion_v31(payload)
    if pipeline_name == "text_only_simple_conversion_v32":
        return run_text_only_simple_conversion_v32(payload)
    if pipeline_name == "text_only_simple_conversion_v33":
        return run_text_only_simple_conversion_v33(payload)
    if pipeline_name == "text_only_simple_conversion_v34":
        return run_text_only_simple_conversion_v34(payload)
    if pipeline_name == "text_only_simple_conversion_v35":
        return run_text_only_simple_conversion_v35(payload)
    if pipeline_name == "text_only_simple_conversion_v36":
        return run_text_only_simple_conversion_v36(payload)
    if pipeline_name == "direct_qa_v1":
        return run_direct_qa_v1(payload)
    if pipeline_name == "direct_qa_conditional_chunk_v1":
        return run_direct_qa_conditional_chunk_v1(payload)
    if pipeline_name == "kg_turtle_extraction_cable_v1":
        return run_kg_turtle_extraction_cable_v1(payload)
    if pipeline_name == "kg_turtle_extraction_pipe_v1":
        return run_kg_turtle_extraction_pipe_v1(payload)
    if pipeline_name == "kg_comprehensive_schema_minimal_turtle_v1":
        return run_kg_comprehensive_schema_minimal_turtle_v1(payload)
    if pipeline_name == "kg_comprehensive_schema_minimal_turtle_v2":
        return run_kg_comprehensive_schema_minimal_turtle_v2(payload)
    if pipeline_name == "kg_comprehensive_schema_minimal_turtle_v3":
        return run_kg_comprehensive_schema_minimal_turtle_v3(payload)
    if pipeline_name == "kg_comprehensive_schema_minimal_turtle_v4":
        return run_kg_comprehensive_schema_minimal_turtle_v4(payload)
    if pipeline_name == "text_image_multimodal_conversion_v11":
        return run_text_image_multimodal_conversion_v11(payload)
    if pipeline_name == "text_image_multimodal_conversion_v19":
        return run_text_image_multimodal_conversion_v19(payload)
    if pipeline_name == "text_image_multimodal_conversion_v21":
        return run_text_image_multimodal_conversion_v21(payload)
    if pipeline_name == "text_image_multimodal_conversion_v22":
        return run_text_image_multimodal_conversion_v22(payload)
    if pipeline_name == "text_image_multimodal_conversion_v23":
        return run_text_image_multimodal_conversion_v23(payload)
    if pipeline_name == "turtle_kg_conversion_v12":
        return run_turtle_kg_conversion_v12(payload)
    if pipeline_name == "turtle_kg_twostep_v13":
        return run_turtle_kg_twostep_v13(payload)
    if pipeline_name == "turtle_kg_keyword_v14":
        return run_turtle_kg_keyword_v14(payload)
    if pipeline_name == "turtle_kg_keyword_v15":
        return run_turtle_kg_keyword_v15(payload)

    supported = (
        "text_only_simple_conversion, text_only_simple_conversion_v2, "
        "text_only_simple_conversion_v3, text_only_simple_conversion_v4, "
        "text_only_simple_conversion_v5, text_only_simple_conversion_v6, "
        "text_only_simple_conversion_v7, text_only_simple_conversion_v8, "
        "text_only_simple_conversion_v9, text_only_simple_conversion_v10, "
        "text_only_simple_conversion_v15, text_only_simple_conversion_v16, "
        "text_only_simple_conversion_v17, text_only_simple_conversion_v18, "
        "text_only_simple_conversion_v20, text_only_simple_conversion_v21, "
        "text_only_simple_conversion_v22, text_only_simple_conversion_v23, "
        "text_only_simple_conversion_v24, text_only_simple_conversion_v25, "
        "text_only_simple_conversion_v26, "
            "text_only_simple_conversion_v27, "
            "text_only_simple_conversion_v28, "
            "text_only_simple_conversion_v29, "
            "text_only_simple_conversion_v30, "
            "text_only_simple_conversion_v33, "
            "text_only_simple_conversion_v31, "
            "text_only_simple_conversion_v32, "
            "text_only_simple_conversion_v34, "
            "text_only_simple_conversion_v35, "
            "text_only_simple_conversion_v36, "
            "direct_qa_v1, direct_qa_conditional_chunk_v1, "
        "kg_turtle_extraction_cable_v1, kg_turtle_extraction_pipe_v1, "
        "kg_comprehensive_schema_minimal_turtle_v1, kg_comprehensive_schema_minimal_turtle_v2, kg_comprehensive_schema_minimal_turtle_v3, "
            "kg_comprehensive_schema_minimal_turtle_v4, "
        "text_image_multimodal_conversion_v11, text_image_multimodal_conversion_v19, "
        "text_image_multimodal_conversion_v21, text_image_multimodal_conversion_v22, "
            "text_image_multimodal_conversion_v23, "
        "turtle_kg_conversion_v12, "
        "turtle_kg_twostep_v13, turtle_kg_keyword_v14, turtle_kg_keyword_v15"
    )
    logger.error(
        "Unsupported pipeline requested: experiment_id=%s pipeline=%s normalized_pipeline=%s supported=%s",
        payload.experiment_id,
        payload.pipeline,
        pipeline_name,
        supported,
    )
    raise ValueError(f"Unsupported pipeline '{payload.pipeline}'. Supported pipelines: {supported}")
