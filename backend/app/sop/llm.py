"""Pluggable LLM client.

Supports OpenAI, Anthropic, a local Ollama endpoint, and an offline ``stub``
provider used for tests and air-gapped demos. Every provider presents the
same :class:`LLMClient` interface so the rest of the code is provider-agnostic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from functools import lru_cache

from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings
from app.core.logging import get_logger

log = get_logger(__name__)


class LLMClient(ABC):
    provider: str = "abstract"

    @abstractmethod
    def complete(self, system: str, user: str, *, max_tokens: int = 1200) -> str: ...


class StubLLMClient(LLMClient):
    """Deterministic offline renderer — useful for tests & demos."""

    provider = "stub"

    def complete(self, system: str, user: str, *, max_tokens: int = 1200) -> str:
        return _stub_render(user)


class OpenAILLMClient(LLMClient):
    provider = "openai"

    def __init__(self, model: str, api_key: str) -> None:
        from openai import OpenAI

        self._client = OpenAI(api_key=api_key)
        self._model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def complete(self, system: str, user: str, *, max_tokens: int = 1200) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=max_tokens,
            temperature=0.2,
        )
        return (resp.choices[0].message.content or "").strip()


class AnthropicLLMClient(LLMClient):
    provider = "anthropic"

    def __init__(self, model: str, api_key: str) -> None:
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    def complete(self, system: str, user: str, *, max_tokens: int = 1200) -> str:
        resp = self._client.messages.create(
            model=self._model,
            system=system,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": user}],
        )
        parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        return "".join(parts).strip()


class OllamaLLMClient(LLMClient):
    provider = "ollama"

    def __init__(self, model: str, base_url: str) -> None:
        import httpx

        self._http = httpx.Client(base_url=base_url, timeout=60)
        self._model = model

    def complete(self, system: str, user: str, *, max_tokens: int = 1200) -> str:
        r = self._http.post(
            "/api/chat",
            json={
                "model": self._model,
                "stream": False,
                "options": {"num_predict": max_tokens, "temperature": 0.2},
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            },
        )
        r.raise_for_status()
        return (r.json().get("message", {}) or {}).get("content", "").strip()


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    provider = settings.llm_provider.lower()
    model = settings.llm_model
    try:
        if provider == "openai" and settings.openai_api_key:
            return OpenAILLMClient(model, settings.openai_api_key)
        if provider == "anthropic" and settings.anthropic_api_key:
            return AnthropicLLMClient(model, settings.anthropic_api_key)
        if provider == "ollama":
            return OllamaLLMClient(model, settings.ollama_base_url)
    except Exception as exc:  # pragma: no cover - init guard
        log.warning("llm.init_failed", provider=provider, error=str(exc))

    log.info("llm.using_stub", reason="provider_unavailable_or_stub")
    return StubLLMClient()


# ---------------------------------------------------------------- stub renderer
_TITLES = {
    "reach": "Reach for component",
    "pick": "Pick up component",
    "place": "Place component in fixture",
    "screw": "Fasten with tool",
    "inspect": "Inspect seating",
    "move": "Move to next sub-station",
    "idle": "Pause / wait",
}
_INSTRUCTIONS = {
    "reach": "Extend the dominant arm toward the component bin. Keep shoulders square to the bench.",
    "pick": "Grasp the component firmly between thumb and forefinger; lift without dragging along the bin wall.",
    "place": "Align the component with the fixture keyway and set it down — do not press.",
    "screw": "Engage the tool, keep the bit perpendicular, drive until the torque clicks.",
    "inspect": "Visually confirm seating and orientation before releasing the part.",
    "move": "Shift weight to the opposite foot and pivot toward the next sub-station.",
    "idle": "Brief pause. No action required.",
}


def _stub_render(user_prompt: str) -> str:
    """Build a reasonable markdown SOP from the structured prompt.

    The real providers produce richer prose; this stub gives a deterministic,
    presentable document so tests / demos stay green offline.
    """
    import json
    import re

    m = re.search(r"<payload>(.*?)</payload>", user_prompt, flags=re.DOTALL)
    data = json.loads(m.group(1)) if m else {}

    title = data.get("title", "Standard Operating Procedure")
    station = data.get("station", "Workstation")
    steps = data.get("steps", [])

    lines = [
        f"# {title}",
        "",
        f"**Station:** {station}  ",
        f"**Target cycle time:** {data.get('target_cycle_time_s', 0):.1f}s  ",
        f"**Version:** 1 (auto-generated from gold-standard reference)",
        "",
        "## Required PPE",
        "",
    ]
    ppe = data.get("required_ppe", []) or ["Safety glasses", "Cut-resistant gloves"]
    for item in ppe:
        lines.append(f"- {item}")
    lines += ["", "## Procedure", ""]

    for i, step in enumerate(steps, 1):
        lbl = step.get("label", "idle")
        dur = float(step.get("target_duration_s", 0))
        lines.append(f"### Step {i}. {_TITLES.get(lbl, lbl.title())}")
        lines.append("")
        lines.append(_INSTRUCTIONS.get(lbl, "Follow the video reference."))
        lines.append("")
        lines.append(f"- **Target duration:** {dur:.2f}s")
        lines.append(f"- **Tolerance:** ±{step.get('tolerance_s', 1.5):.1f}s")
        lines.append("")

    lines += [
        "## Safety & quality notes",
        "",
        "- Stop the line immediately if any step runs >2× its target duration.",
        "- PPE must remain worn for the entire cycle — the system will alert on violations.",
        "- Report any deviation in part seating during **Inspect** to your supervisor.",
    ]
    return "\n".join(lines)
