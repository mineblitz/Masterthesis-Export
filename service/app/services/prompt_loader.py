from pathlib import Path

from app.settings import settings


def load_prompt_template(prompt_name: str) -> str:
    prompt_path = Path(settings.prompts_dir) / prompt_name
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")
