"""Real-time compliance engine.

Feeds an action-score stream through a set of rules, persists any raised
alerts, and optionally pushes them onto a Redis pub/sub channel so the API's
WebSocket handler can broadcast them to supervisors.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import AsyncIterator, Iterable, Iterator

from sqlalchemy.orm import Session

from app.alerts.rules import BaseRule, RuleResult, default_rules
from app.core.logging import get_logger
from app.models.alert import Alert
from app.models.session import MonitoringSession
from app.models.sop import SOP
from app.vision.types import ActionScore

log = get_logger(__name__)


@dataclass
class EngineEvent:
    kind: str  # "score" | "alert"
    payload: dict

    def to_json(self) -> str:
        return json.dumps({"kind": self.kind, **self.payload}, default=str)


class ComplianceEngine:
    def __init__(
        self,
        sop: SOP,
        *,
        rules: Iterable[BaseRule] | None = None,
    ) -> None:
        self.sop = sop
        self.rules: list[BaseRule] = list(rules) if rules is not None else default_rules(sop)

    # ---------------------------------------------------------------- sync
    def run(
        self,
        scores: Iterable[ActionScore],
        *,
        db: Session | None = None,
        session: MonitoringSession | None = None,
    ) -> Iterator[EngineEvent]:
        """Iterate scores, yielding engine events (score + any alerts).

        If ``db`` and ``session`` are provided, alerts are also persisted as
        :class:`Alert` rows. The caller is responsible for committing.
        """
        for s in scores:
            yield EngineEvent("score", {"timestamp_s": s.timestamp_s, "label": s.top_label, "confidence": s.top_score})

            for rule in self.rules:
                for hit in rule.observe(s):
                    alert_payload = asdict(hit)
                    alert_payload["severity"] = hit.severity.value
                    yield EngineEvent("alert", alert_payload)
                    if db is not None and session is not None:
                        db.add(
                            Alert(
                                session_id=session.id,
                                rule=hit.rule,
                                severity=hit.severity,
                                title=hit.title,
                                message=hit.message,
                                at_s=hit.at_s,
                                evidence=hit.evidence,
                            )
                        )

        # finalisation — fires once at end-of-session
        for rule in self.rules:
            for hit in rule.finalise():
                alert_payload = asdict(hit)
                alert_payload["severity"] = hit.severity.value
                yield EngineEvent("alert", alert_payload)
                if db is not None and session is not None:
                    db.add(
                        Alert(
                            session_id=session.id,
                            rule=hit.rule,
                            severity=hit.severity,
                            title=hit.title,
                            message=hit.message,
                            at_s=hit.at_s,
                            evidence=hit.evidence,
                        )
                    )

    # --------------------------------------------------------------- async
    async def run_async(self, scores: AsyncIterator[ActionScore]) -> AsyncIterator[EngineEvent]:
        async for s in scores:
            yield EngineEvent(
                "score",
                {"timestamp_s": s.timestamp_s, "label": s.top_label, "confidence": s.top_score},
            )
            for rule in self.rules:
                for hit in rule.observe(s):
                    payload = asdict(hit)
                    payload["severity"] = hit.severity.value
                    yield EngineEvent("alert", payload)
