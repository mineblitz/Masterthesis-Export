from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


ExpectedValue = float | str | dict[str, Any] | list[dict[str, Any]] | None


class LLMProvider(str, Enum):
    """Available LLM providers."""
    HAWKI = "hawki"
    OPENAI = "openai"
    LOCALAI = "localai"
    OPENROUTER = "openrouter"
    # Future providers can be added here (e.g., ANTHROPIC, HUGGINGFACE, etc.)


class LLMModel(str, Enum):
    """
    Available LLM models across all providers.
    Format: provider:model_name
    Adding new providers: create enum values with the pattern "new_provider:model_name"
    """
    # HAWKI wrapper models (wraps various open/closed source models)
    HAWKI_GPT_4O = "hawki:gpt-4o"
    HAWKI_GPT_4O_MINI = "hawki:gpt-4o-mini"
    HAWKI_O1_MINI = "hawki:o1-mini"
    HAWKI_LLAMA_3_1_8B = "hawki:meta-llama-3.1-8b-instruct"
    HAWKI_LLAMA_3_1_70B = "hawki:meta-llama-3.1-70b-instruct"
    HAWKI_MISTRAL_LARGE = "hawki:mistral-large-instruct"
    HAWKI_GEMINI_1_5_FLASH = "hawki:gemini-1.5-flash"
    HAWKI_GEMINI_2_0_FLASH = "hawki:gemini-2.0-flash-lite"
    HAWKI_GEMINI_2_5_PRO = "hawki:gemini-2.5-pro-exp-03-25"

    # OpenAI direct models (for future expansion)
    OPENAI_GPT_4O = "openai:gpt-4o"

    # LocalAI models (OpenAI-compatible local endpoint)
    LOCALAI_GEMMA_3_27B_IT = "localai:gemma-3-27b-it"
    LOCALAI_GEMMA_4_31B_IT = "localai:gemma-4-31b-it"

    # OpenRouter models
    OPENROUTER_GEMMA_4_26B_A4B_IT_FREE = "openrouter:google/gemma-4-26b-a4b-it:free"
    OPENROUTER_GEMMA_4_26B_A4B_IT = "openrouter:google/gemma-4-26b-a4b-it"
    OPENROUTER_QWEN_QWEN3_6_PLUS = "openrouter:qwen/qwen3.6-plus"
    OPENROUTER_QWEN_QWEN3_5_FLASH_02_23 = "openrouter:qwen/qwen3.5-flash-02-23"
    OPENROUTER_ANTHROPIC_CLAUDE_OPUS_4_7 = "openrouter:anthropic/claude-opus-4.7"
    OPENROUTER_ANTHROPIC_CLAUDE_OPUS_5_5 = "openrouter:anthropic/claude-opus-5.5"
    OPENROUTER_GOOGLE_GEMMA_4_31B_IT = "openrouter:google/gemma-4-31b-it"
    OPENROUTER_GOOGLE_GEMINI_3_1_PRO_PREVIEW = "openrouter:google/gemini-3.1-pro-preview"
    OPENROUTER_GOOGLE_GEMINI_4_ARGON = "openrouter:google/gemini-4-argon"
    OPENROUTER_OPENAI_GPT_OSS_120B = "openrouter:openai/gpt-oss-120b"
    OPENROUTER_OPENAI_GPT_5_4 = "openrouter:openai/gpt-5.4"
    OPENROUTER_OPENAI_GPT_6_ASTRA = "openrouter:openai/gpt-6-astra"
    OPENROUTER_OPENAI_GPT_6_1_SOL = "openrouter:openai/gpt-6.1-sol"
    OPENROUTER_MOONSHOTAI_KIMI_K2_6 = "openrouter:moonshotai/kimi-k2.6"
    OPENROUTER_X_AI_GROK_4_3 = "openrouter:x-ai/grok-4.3"
    OPENROUTER_TENCENT_HY3_PREVIEW = "openrouter:tencent/hy3-preview"
    OPENROUTER_DEEPSEEK_DEEPSEEK_V3_2 = "openrouter:deepseek/deepseek-v3.2"
    OPENROUTER_DEEPSEEK_DEEPSEEK_V4_FLASH_LATEST = "openrouter:~deepseek/deepseek-v4-flash-latest"
    OPENROUTER_DEEPSEEK_DEEPSEEK_V4_1_FLASH_1017 = "openrouter:deepseek/deepseek-v4.1-flash-1017"
    OPENROUTER_MINIMAX_MINIMAX_M2_7 = "openrouter:minimax/minimax-m2.7"
    OPENROUTER_MINIMAX_MINIMAX_M3_1_FLASH = "openrouter:minimax/minimax-m3.1-flash"
    OPENROUTER_XIAOMI_MIMO_V2_5_PRO = "openrouter:xiaomi/mimo-v2.5-pro"

    @classmethod
    def parse_identifier(cls, value: str) -> "LLMModel":
        # Canonical format is enum-name (e.g. HAWKI_GPT_4O), value format is also accepted.
        legacy_aliases = {
            cls.LOCALAI_GEMMA_3_27B_IT.name.casefold(),
            cls.LOCALAI_GEMMA_3_27B_IT.value.casefold(),
            cls.LOCALAI_GEMMA_3_27B_IT.value.split(":", 1)[1].casefold(),
        }
        if value.casefold() in legacy_aliases:
            return cls.LOCALAI_GEMMA_4_31B_IT
        if value in cls.__members__:
            return cls[value]
        return cls(value)


class ExperimentRequest(BaseModel):
    class Condition(BaseModel):
        id: int | None = None
        type: str
        value: str

        model_config = ConfigDict(extra="allow")

    pipeline: str
    llm: LLMModel
    experiment_id: str
    experiment_name: str
    experiment_description: str | None = None
    temperature: float | None = None
    prompt: str
    answer_output_mode: Literal["numeric", "verbatim"] = "numeric"

    order: int | None = None
    min_or_max: str | None = None
    value: str
    conditions: list[Condition] | None = None
    conditions_turtle: str | None = None
    system: str = ""
    system_name: str = ""
    approval_links: list[str] = []
    content: str | None = None
    question: str | None = None
    expected_value: ExpectedValue = None
    created_at: str | None = None
    number_of_variables_per_request: int | None = None

    @model_validator(mode="before")
    @classmethod
    def normalize_external_keys(cls, value: Any) -> Any:
        if not isinstance(value, dict):
            return value

        mapped = dict(value)
        alias_to_field = {
            "LLM": "llm",
            "experiment_ID": "experiment_id",
            "experiment_Name": "experiment_name",
            "experiment_Description": "experiment_description",
            "experimentId": "experiment_id",
            "experimentName": "experiment_name",
            "experimentDescription": "experiment_description",
            "minOrMax": "min_or_max",
            "systemName": "system_name",
            "approvalLinks": "approval_links",
            "chunk": "content",
            "expectedValue": "expected_value",
            "createdAt": "created_at",
            "conditionsTurtle": "conditions_turtle",
            "numberOfVariablesPerRequest": "number_of_variables_per_request",
        }
        for alias_key, field_key in alias_to_field.items():
            if alias_key in mapped and field_key not in mapped:
                mapped[field_key] = mapped[alias_key]

        return mapped

    @field_validator("llm", mode="before")
    @classmethod
    def parse_llm(cls, value: Any) -> LLMModel:
        if isinstance(value, LLMModel):
            return LLMModel.parse_identifier(value.value)
        if isinstance(value, str):
            return LLMModel.parse_identifier(value)
        raise ValueError("LLM must be a string")

    @model_validator(mode="after")
    def validate_pipeline_fields(self) -> "ExperimentRequest":
        # For legacy pipelines min_or_max is still required, while newer versions
        # can work with explicit conditions and no min/max selector.
        legacy_pipelines = {
            "text_only_simple_conversion",
            "text_only_simple_conversion_v2",
            "text_only_simple_conversion_v3",
        }
        if self.pipeline in legacy_pipelines and not self.min_or_max:
            raise ValueError("min_or_max is required for pipeline versions before v4")
        return self

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ComponentLog(BaseModel):
    name: str
    status: str
    started_at: str
    finished_at: str
    input_tokens: int = 0
    output_tokens: int = 0
    details: dict[str, Any] | None = None
    error: str | None = None


class ExperimentResult(BaseModel):
    expected_value: ExpectedValue
    extracted_value: ExpectedValue
    is_match: bool
    confidence: float | None = None
    full_prompt: str
    full_output: str
    input_tokens: int
    output_tokens: int
    temperature: float | None
    experiment_id: str
    pipeline_started_at: str
    pipeline_finished_at: str
    experiment_description: str | None
    used_documents: list[str]
    system: str
    extracted_value_type: str
    min_or_max: str | None
    used_llm: str
    components: list[ComponentLog]


class ExperimentResponse(BaseModel):
    status: str
    experiment_id: str
    pipeline: str
    result: ExperimentResult


class LLMTextRequest(BaseModel):
    """Request for text generation from LLM."""
    prompt: str
    llm: LLMModel
    max_tokens: int | None = None
    temperature: float | None = None


class LLMTextResponse(BaseModel):
    """Response from LLM text generation."""
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
