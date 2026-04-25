"""Tests for the deterministic stub LLM renderer."""
from __future__ import annotations

import json

from app.sop.llm import StubLLMClient


def _prompt(payload: dict) -> str:
    return (
        "Generate the SOP for the following gold-standard reference. "
        "Respond with Markdown only, no preface.\n\n"
        f"<payload>{json.dumps(payload)}</payload>"
    )


def test_stub_renders_title_station_and_steps():
    payload = {
        "title": "Door-handle assembly",
        "station": "S3",
        "required_ppe": ["glasses", "glove"],
        "target_cycle_time_s": 7.5,
        "steps": [
            {"label": "pick", "target_duration_s": 2.0, "tolerance_s": 0.5},
            {"label": "place", "target_duration_s": 2.0, "tolerance_s": 0.5},
            {"label": "screw", "target_duration_s": 3.0, "tolerance_s": 1.0},
        ],
    }
    md = StubLLMClient().complete("sys", _prompt(payload))

    assert md.startswith("# Door-handle assembly")
    assert "**Station:** S3" in md
    assert "7.5s" in md
    # every step becomes its own heading
    assert "### Step 1. Pick up component" in md
    assert "### Step 2. Place component in fixture" in md
    assert "### Step 3. Fasten with tool" in md
    # PPE list is included
    assert "- glasses" in md
    assert "- glove" in md
    # safety footer is always present
    assert "Safety & quality notes" in md


def test_stub_supplies_default_ppe_when_empty():
    payload = {"title": "t", "station": "s", "steps": [], "required_ppe": []}
    md = StubLLMClient().complete("sys", _prompt(payload))
    assert "Safety glasses" in md
    assert "Cut-resistant gloves" in md


def test_stub_is_deterministic():
    payload = {
        "title": "deterministic",
        "station": "S1",
        "steps": [{"label": "pick", "target_duration_s": 1.0, "tolerance_s": 0.2}],
        "required_ppe": [],
    }
    a = StubLLMClient().complete("sys", _prompt(payload))
    b = StubLLMClient().complete("sys", _prompt(payload))
    assert a == b
