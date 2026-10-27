"""Cable KG Turtle extraction pipeline."""

from app.models import ExperimentRequest, ExperimentResponse
from app.services.components.json_husk_renderer_component import (
    render_cable_records_to_json_husk,
)
from app.services.components.turtle_husk_renderer_component import (
    render_cable_records_to_turtle,
)
from app.services.pipelines._kg_turtle_extraction_common import run_kg_turtle_extraction


_CABLE_FIELD_SCHEMA = {
    "purpose_name": "string",
    "min_diameter": "number",
    "max_diameter": "number",
}


def run_kg_turtle_extraction_cable_v1(payload: ExperimentRequest) -> ExperimentResponse:
    return run_kg_turtle_extraction(
        payload,
        field_schema=_CABLE_FIELD_SCHEMA,
        turtle_renderer=render_cable_records_to_turtle,
        json_renderer=render_cable_records_to_json_husk,
        prompt_builder_name="kg_turtle_extraction_cable_v1.txt",
        entity_type="cable",
    )