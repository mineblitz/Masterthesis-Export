from __future__ import annotations

import base64
import json
from io import BytesIO
from typing import Annotated, List

import PIL
from openai import OpenAI
from pydantic import BaseModel

from marker.schema.blocks import Block
from marker.services import BaseService


class OpenAICompatService(BaseService):
    openai_base_url: Annotated[
        str,
        "The OpenAI-compatible base URL to use for requests.",
    ] = "http://localhost:8080/v1"
    openai_api_key: Annotated[
        str,
        "The API key for the OpenAI-compatible service.",
    ] = "not-needed"
    openai_model: Annotated[
        str,
        "The model name to use for completion requests.",
    ] = "gemma-3-27b"

    @staticmethod
    def _image_to_data_url(image: PIL.Image.Image) -> str:
        image_bytes = BytesIO()
        image.save(image_bytes, format="PNG")
        encoded = base64.b64encode(image_bytes.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"

    @staticmethod
    def _parse_json_payload(content: str) -> dict:
        try:
            data = json.loads(content)
            return data if isinstance(data, dict) else {}
        except Exception:
            start = content.find("{")
            end = content.rfind("}")
            if start >= 0 and end > start:
                try:
                    data = json.loads(content[start : end + 1])
                    return data if isinstance(data, dict) else {}
                except Exception:
                    return {}
        return {}

    def __call__(
        self,
        prompt: str,
        image: PIL.Image.Image | List[PIL.Image.Image],
        block: Block,
        response_schema: type[BaseModel],
        max_retries: int | None = None,
        timeout: int | None = None,
    ):
        if max_retries is None:
            max_retries = self.max_retries

        if timeout is None:
            timeout = self.timeout

        if not isinstance(image, list):
            image = [image]

        content_parts: list[dict] = [{"type": "text", "text": prompt}]
        for img in image:
            content_parts.append(
                {
                    "type": "image_url",
                    "image_url": {"url": self._image_to_data_url(img)},
                }
            )

        client = OpenAI(base_url=self.openai_base_url, api_key=self.openai_api_key)

        tries = 0
        while tries < max_retries:
            try:
                completion = client.chat.completions.create(
                    model=self.openai_model,
                    messages=[{"role": "user", "content": content_parts}],
                    response_format={"type": "json_object"},
                    timeout=timeout,
                )

                message = completion.choices[0].message.content or "{}"
                result = self._parse_json_payload(message)

                prompt_tokens = completion.usage.prompt_tokens if completion.usage else 0
                completion_tokens = completion.usage.completion_tokens if completion.usage else 0
                block.update_metadata(
                    llm_request_count=1,
                    llm_tokens_used=prompt_tokens + completion_tokens,
                )
                return result
            except Exception as exc:
                tries += 1
                if tries >= max_retries:
                    print(f"OpenAI-compatible inference failed: {exc}")
                    break

        return {}
