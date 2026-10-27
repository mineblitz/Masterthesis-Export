import tiktoken

_encoder = None


def _get_encoder():
    """Lazy-load tiktoken encoder for GPT-like models."""
    global _encoder
    if _encoder is None:
        _encoder = tiktoken.get_encoding("cl100k_base")
    return _encoder


def count_tokens(text: str) -> int:
    """Count tokens using tiktoken (accurate for GPT-3.5/GPT-4 models)."""
    if not text:
        return 0
    encoder = _get_encoder()
    return len(encoder.encode(text))
