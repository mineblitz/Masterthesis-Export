import logging
import mimetypes
import time
import base64
from pathlib import Path
from typing import Any

from openai import OpenAI

from app.models import LLMModel, LLMProvider, LLMTextResponse
from app.settings import settings
from app.services.token_counter import count_tokens


logger = logging.getLogger("app.llm_client")
logger.setLevel(logging.DEBUG)

_OPENROUTER_MODEL_MAX_OUTPUT_TOKENS = {
    "google/gemini-4-argon": 6000,
    "qwen/qwen3.6-plus": 6500,
    "minimax/minimax-m3.1-flash": 6500,
}


def _resolve_openrouter_max_tokens(model_name: str, max_tokens: int | None) -> int | None:
    model_limit = _OPENROUTER_MODEL_MAX_OUTPUT_TOKENS.get(model_name)
    if model_limit is None:
        return max_tokens
    if max_tokens is None:
        return model_limit
    return min(max_tokens, model_limit)


class LLMClient:
    """Multi-provider LLM client with OpenAI-compatible backends."""

    def __init__(self) -> None:
        """Initialize provider clients."""
        # HAWKI client: OpenAI SDK pointing to HAWKI wrapper
        self.hawki_client = OpenAI(
            base_url=settings.hawki_base_url,
            api_key=settings.hawki_api_key,
        )
        self.hawki_timeout = settings.hawki_request_timeout

        # LocalAI client: OpenAI-compatible local endpoint
        self.localai_client = OpenAI(
            base_url=settings.localai_base_url,
            api_key=settings.localai_api_key,
        )
        self.localai_timeout = settings.localai_request_timeout
        self.localai_retry_attempts = max(1, settings.localai_retry_attempts)
        self.localai_retry_backoff_seconds = max(0.0, settings.localai_retry_backoff_seconds)

        # OpenRouter client: OpenAI-compatible endpoint for multimodal models
        self.openrouter_api_key = settings.openrouter_api_key or settings.open_router_api_key
        self.openrouter_client = OpenAI(
            base_url=settings.openrouter_base_url,
            api_key=self.openrouter_api_key or "",
        )
        self.openrouter_timeout = settings.openai_request_timeout
        
        # OpenAI client: To be initialized when openai_api_key is provided
        # self.openai_client = None
        # if settings.openai_api_key:
        #     self.openai_client = OpenAI(api_key=settings.openai_api_key)

    @staticmethod
    @staticmethod
    def _is_retryable_llm_error(exc: Exception) -> bool:
        """Detect transient transport/provider failures worth retrying."""
        status_code = getattr(exc, "status_code", None)
        if isinstance(status_code, int) and status_code in {408, 429, 500, 502, 503, 504}:
            return True

        message = str(exc).lower()
        retryable_markers = [
            "504",
            "503",
            "502",
            "gateway time-out",
            "gateway timeout",
            "timed out",
            "timeout",
            "connection reset",
            "temporarily unavailable",
            "rate limit",
            "too many requests",
        ]
        return any(marker in message for marker in retryable_markers)

    @staticmethod
    def _rate_limit_wait_seconds(exc: Exception, backoff_seconds: float) -> float:
        """Return how many seconds to wait before the next retry.

        If the exception carries an X-RateLimit-Reset header (milliseconds epoch),
        we wait until that timestamp plus a 1 s buffer.  Otherwise fall back to
        the caller-supplied backoff_seconds.
        """
        import time as _time
        response = getattr(exc, "response", None)
        if response is not None:
            headers = getattr(response, "headers", {})
            reset_ms = headers.get("X-RateLimit-Reset")
            if reset_ms is not None:
                try:
                    reset_epoch_s = int(reset_ms) / 1000.0
                    remaining = reset_epoch_s - _time.time() + 1.0
                    if remaining > 0:
                        return remaining
                except (ValueError, TypeError):
                    pass
        return backoff_seconds

    def _create_chat_completion_with_retry(
        self,
        *,
        client: OpenAI,
        provider_name: str,
        model_name: str,
        prompt: str,
        max_tokens: int | None,
        temperature: float | None,
        timeout_seconds: int,
        attempts: int,
        backoff_seconds: float,
    ):
        """Create chat completion with retries for transient upstream failures."""
        for attempt in range(1, attempts + 1):
            try:
                return client.chat.completions.create(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout_seconds,
                )
            except Exception as exc:
                retryable = self._is_retryable_llm_error(exc)
                is_last_attempt = attempt >= attempts
                if not retryable or is_last_attempt:
                    raise

                wait_seconds = self._rate_limit_wait_seconds(exc, backoff_seconds * (2 ** (attempt - 1)))
                logger.warning(
                    "%s API transient failure on attempt %d/%d for model=%s. Retrying in %.1fs. Error=%s",
                    provider_name,
                    attempt,
                    attempts,
                    model_name,
                    wait_seconds,
                    str(exc),
                )
                if wait_seconds > 0:
                    time.sleep(wait_seconds)

    def _create_chat_completion_with_retry_messages(
        self,
        *,
        client: OpenAI,
        provider_name: str,
        model_name: str,
        messages: list[dict[str, Any]],
        max_tokens: int | None,
        temperature: float | None,
        timeout_seconds: int,
        attempts: int,
        backoff_seconds: float,
    ):
        """Create chat completion with arbitrary message payload and retries."""
        for attempt in range(1, attempts + 1):
            try:
                return client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    timeout=timeout_seconds,
                )
            except Exception as exc:
                retryable = self._is_retryable_llm_error(exc)
                is_last_attempt = attempt >= attempts
                if not retryable or is_last_attempt:
                    raise

                wait_seconds = self._rate_limit_wait_seconds(exc, backoff_seconds * (2 ** (attempt - 1)))
                logger.warning(
                    "%s API transient failure on attempt %d/%d for model=%s. Retrying in %.1fs. Error=%s",
                    provider_name,
                    attempt,
                    attempts,
                    model_name,
                    wait_seconds,
                    str(exc),
                )
                if wait_seconds > 0:
                    time.sleep(wait_seconds)
                continue

    @staticmethod
    def _build_image_data_url(path: Path) -> str:
        """Encode an image file to data URL for OpenAI-compatible multimodal requests."""
        mime_type, _ = mimetypes.guess_type(path.name)
        if not mime_type:
            mime_type = "image/jpeg"
        b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
        return f"data:{mime_type};base64,{b64}"

    def _parse_model(self, llm: LLMModel) -> tuple[LLMProvider, str]:
        """Parse model identifier to extract provider and model name.
        
        Args:
            llm: LLMModel enum value (format: provider:model_name)
            
        Returns:
            Tuple of (provider, model_name)
        """
        model_identifier = getattr(llm, "value", None)
        if not isinstance(model_identifier, str) or ":" not in model_identifier:
            raise ValueError(
                f"Invalid model format: {model_identifier}. Expected 'provider:model_name'"
            )
        parts = model_identifier.split(":", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid model format: {llm.value}. Expected 'provider:model_name'")
        
        provider_str, model_name = parts
        try:
            provider = LLMProvider(provider_str)
        except ValueError:
            raise ValueError(f"Unknown LLM provider: {provider_str}")
        
        return provider, model_name

    def generate_text(
        self,
        prompt: str,
        llm: LLMModel,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMTextResponse:
        """Generate text using the specified LLM model.

        Args:
            prompt: Text prompt to send to the LLM.
            llm: LLMModel enum specifying which model to use (format: provider:model_name).
            max_tokens: Optional max tokens in response.
            temperature: Optional temperature for sampling (0.0 to 2.0).

        Returns:
            LLMTextResponse with generated text and usage metadata.

        Raises:
            ValueError: If model format or provider is invalid.
            RuntimeError: If API call fails (e.g., 401, 503, 504).
        """
        llm = LLMModel.parse_identifier(llm.value)
        provider, model_name = self._parse_model(llm)
        if provider == LLMProvider.OPENROUTER:
            max_tokens = _resolve_openrouter_max_tokens(model_name, max_tokens)
        logger.debug(
            "LLM generate_text called: provider=%s model=%s max_tokens=%s temperature=%s prompt_length=%d",
            provider.value,
            model_name,
            max_tokens,
            temperature,
            len(prompt),
        )
        
        if provider == LLMProvider.HAWKI:
            return self._generate_hawki(prompt, llm, model_name, max_tokens, temperature)
        elif provider == LLMProvider.LOCALAI:
            return self._generate_localai(prompt, llm, model_name, max_tokens, temperature)
        elif provider == LLMProvider.OPENROUTER:
            return self._generate_openrouter_text(prompt, llm, model_name, max_tokens, temperature)
        elif provider == LLMProvider.OPENAI:
            return self._generate_openai(prompt, llm, model_name, max_tokens, temperature)
        else:
            raise NotImplementedError(f"Provider {provider.value} not yet implemented")

    def generate_multimodal(
        self,
        prompt: str,
        image_paths: list[str],
        llm: LLMModel,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> LLMTextResponse:
        """Generate text using prompt + images for providers that support multimodal inputs."""
        provider, model_name = self._parse_model(llm)
        if provider != LLMProvider.OPENROUTER:
            raise ValueError(
                f"Multimodal generation currently supports only openrouter models. Got {llm.value}"
            )

        if not self.openrouter_api_key:
            raise ValueError(
                "OpenRouter API key missing. Set OPEN_ROUTER_API_KEY (or open_router_api_key) in .env."
            )

        if not image_paths:
            raise ValueError("Multimodal generation requires at least one image path")

        max_tokens = _resolve_openrouter_max_tokens(model_name, max_tokens)
        content_parts: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        for image_path in image_paths:
            path = Path(image_path)
            if not path.exists():
                logger.warning("Skipping missing multimodal image: %s", image_path)
                continue
            content_parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self._build_image_data_url(path)},
                }
            )

        if len(content_parts) == 1:
            raise ValueError("No readable image files found for multimodal generation")

        messages: list[dict[str, Any]] = [{"role": "user", "content": content_parts}]
        try:
            completion = self._create_chat_completion_with_retry_messages(
                client=self.openrouter_client,
                provider_name="OpenRouter",
                model_name=model_name,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout_seconds=self.openrouter_timeout,
                attempts=settings.openrouter_retry_attempts,
                backoff_seconds=settings.openrouter_retry_backoff_seconds,
            )
        except Exception as exc:
            logger.exception("OpenRouter multimodal API call failed: model=%s", llm.value)
            raise RuntimeError(
                f"OpenRouter multimodal API call failed for model {llm.value}: {str(exc)}"
            ) from exc

        response_text = completion.choices[0].message.content or ""
        input_tokens = 0
        output_tokens = 0
        if completion.usage:
            input_tokens = completion.usage.prompt_tokens or 0
            output_tokens = completion.usage.completion_tokens or 0

        if input_tokens == 0:
            input_tokens = count_tokens(prompt)
        if output_tokens == 0:
            output_tokens = count_tokens(response_text)

        return LLMTextResponse(
            text=response_text,
            model=llm.value,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    def _generate_hawki(
        self,
        prompt: str,
        llm: LLMModel,
        model_name: str,
        max_tokens: int | None,
        temperature: float | None,
    ) -> LLMTextResponse:
        """Generate text using HAWKI wrapper."""
        try:
            logger.debug(
                "Calling HAWKI API: model=%s timeout=%s",
                model_name,
                self.hawki_timeout,
            )
            completion = self._create_chat_completion_with_retry(
                client=self.hawki_client,
                provider_name="HAWKI",
                model_name=model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout_seconds=self.hawki_timeout,
                attempts=self.localai_retry_attempts,
                backoff_seconds=self.localai_retry_backoff_seconds,
            )
        except Exception as exc:
            logger.exception("HAWKI API call failed: model=%s", llm.value)
            raise RuntimeError(
                f"HAWKI LLM API call failed for model {llm.value}: {str(exc)}"
            ) from exc

        response_text = completion.choices[0].message.content or ""
        input_tokens = 0
        output_tokens = 0
        if completion.usage:
            input_tokens = completion.usage.prompt_tokens or 0
            output_tokens = completion.usage.completion_tokens or 0

        if input_tokens == 0:
            input_tokens = count_tokens(prompt)
        if output_tokens == 0:
            output_tokens = count_tokens(response_text)

        return LLMTextResponse(
            text=response_text,
            model=llm.value,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    def _generate_localai(
        self,
        prompt: str,
        llm: LLMModel,
        model_name: str,
        max_tokens: int | None,
        temperature: float | None,
    ) -> LLMTextResponse:
        """Generate text using LocalAI OpenAI-compatible API."""
        try:
            logger.debug(
                "Calling LocalAI API: model=%s timeout=%s attempts=%d backoff=%.1fs",
                model_name,
                self.localai_timeout,
                self.localai_retry_attempts,
                self.localai_retry_backoff_seconds,
            )
            completion = self._create_chat_completion_with_retry(
                client=self.localai_client,
                provider_name="LocalAI",
                model_name=model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout_seconds=self.localai_timeout,
                attempts=self.localai_retry_attempts,
                backoff_seconds=self.localai_retry_backoff_seconds,
            )
        except Exception as exc:
            logger.exception("LocalAI API call failed: model=%s", llm.value)
            raise RuntimeError(
                f"LocalAI LLM API call failed for model {llm.value}: {str(exc)}"
            ) from exc

        response_text = completion.choices[0].message.content or ""
        input_tokens = 0
        output_tokens = 0
        if completion.usage:
            input_tokens = completion.usage.prompt_tokens or 0
            output_tokens = completion.usage.completion_tokens or 0

        if input_tokens == 0:
            input_tokens = count_tokens(prompt)
        if output_tokens == 0:
            output_tokens = count_tokens(response_text)

        return LLMTextResponse(
            text=response_text,
            model=llm.value,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )

    def _generate_openai(
        self,
        prompt: str,
        llm: LLMModel,
        model_name: str,
        max_tokens: int | None,
        temperature: float | None,
    ) -> LLMTextResponse:
        """Generate text using OpenAI API.
        
        TODO: Implement when openai_api_key is provided in settings.
        """
        raise NotImplementedError(
            f"OpenAI provider ({llm.value}) not yet implemented. "
            "Please configure openai_api_key in settings."
        )

    def _generate_openrouter_text(
        self,
        prompt: str,
        llm: LLMModel,
        model_name: str,
        max_tokens: int | None,
        temperature: float | None,
    ) -> LLMTextResponse:
        """Generate text using OpenRouter with OpenAI-compatible API."""
        if not self.openrouter_api_key:
            raise ValueError(
                "OpenRouter API key missing. Set OPEN_ROUTER_API_KEY (or open_router_api_key) in .env."
            )

        try:
            logger.debug(
                "Calling OpenRouter API (text): model=%s timeout=%s",
                model_name,
                self.openrouter_timeout,
            )
            completion = self._create_chat_completion_with_retry(
                client=self.openrouter_client,
                provider_name="OpenRouter",
                model_name=model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout_seconds=self.openrouter_timeout,
                attempts=settings.openrouter_retry_attempts,
                backoff_seconds=settings.openrouter_retry_backoff_seconds,
            )
        except Exception as exc:
            logger.exception("OpenRouter API call failed: model=%s", llm.value)
            raise RuntimeError(
                f"OpenRouter LLM API call failed for model {llm.value}: {str(exc)}"
            ) from exc

        response_text = completion.choices[0].message.content or ""
        input_tokens = 0
        output_tokens = 0
        if completion.usage:
            input_tokens = completion.usage.prompt_tokens or 0
            output_tokens = completion.usage.completion_tokens or 0

        if input_tokens == 0:
            input_tokens = count_tokens(prompt)
        if output_tokens == 0:
            output_tokens = count_tokens(response_text)

        return LLMTextResponse(
            text=response_text,
            model=llm.value,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
        )


llm_client = LLMClient()
