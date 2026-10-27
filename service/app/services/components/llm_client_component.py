"""LLM client component wrapper for text generation."""
from app.models import LLMModel, LLMTextResponse
from app.services.llm_client import llm_client


def generate_text_component(
    prompt: str,
    llm: LLMModel,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> LLMTextResponse:
    """
    Wrapper around the shared llm_client with consistent error handling.
    
    Args:
        prompt: Text prompt to send to the LLM.
        llm: LLMModel enum specifying which model to use.
        temperature: Optional temperature for sampling.
        max_tokens: Optional max tokens in response.
        
    Returns:
        LLMTextResponse with generated text and usage metadata.
        
    Raises:
        RuntimeError: If API call fails.
    """
    return llm_client.generate_text(
        prompt=prompt,
        llm=llm,
        temperature=temperature,
        max_tokens=max_tokens,
    )


def generate_multimodal_component(
    prompt: str,
    image_paths: list[str],
    llm: LLMModel,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> LLMTextResponse:
    """Wrapper around shared llm_client for text+image multimodal generation."""
    return llm_client.generate_multimodal(
        prompt=prompt,
        image_paths=image_paths,
        llm=llm,
        temperature=temperature,
        max_tokens=max_tokens,
    )
