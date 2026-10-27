"""Pipe KG Turtle extraction pipeline."""

from app.models import ExperimentRequest, ExperimentResponse
from app.services.components.json_husk_renderer_component import render_pipe_records_to_json_husk
from app.services.components.turtle_husk_renderer_component import render_pipe_records_to_turtle
from app.services.pipelines._kg_turtle_extraction_common import run_kg_turtle_extraction


_PIPE_FIELD_SCHEMA = {
    "purpose_name": "string",
    "material_name": "string",
    "isolation_type_name": "string",
    "transfer_category_name": "string",
    "min_diameter": "number",
    "max_diameter": "number",
    "pipe_type_names": "string_list",
}


def run_kg_turtle_extraction_pipe_v1(payload: ExperimentRequest) -> ExperimentResponse:
    return run_kg_turtle_extraction(
        payload,
        field_schema=_PIPE_FIELD_SCHEMA,
        turtle_renderer=render_pipe_records_to_turtle,
        json_renderer=render_pipe_records_to_json_husk,
        prompt_builder_name="kg_turtle_extraction_pipe_v1.txt",
        entity_type="pipe",
    )