"""VLM Processor — call Qwen VLM API (OpenAI-compatible) for image descriptions."""
import base64
import io
import httpx
from pathlib import Path
from PIL import Image
from shared.config import settings

_PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
_DEFAULT_PROMPT = "Describe this satellite image in detail suitable for search indexing."


def _load_prompt() -> str:
    prompt_file = _PROMPT_DIR / "vlm_prompt_v1.txt"
    try:
        return prompt_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return _DEFAULT_PROMPT


def _resize_and_encode(image_bytes: bytes, max_edge: int = 1024) -> str:
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((max_edge, max_edge))
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception:
        return base64.b64encode(image_bytes).decode("utf-8")


def generate_description(image_bytes: bytes) -> str:
    image_b64 = _resize_and_encode(image_bytes)
    prompt_text = _load_prompt()

    payload = {
        "model": "Qwen/Qwen2-VL-7B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt_text},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
                ],
            }
        ],
        "max_tokens": 1024,
        "temperature": 0.1,
    }

    url = settings.VLM_URL.rstrip("/") + "/v1/chat/completions"
    with httpx.Client(timeout=120.0) as client:
        resp = client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]
