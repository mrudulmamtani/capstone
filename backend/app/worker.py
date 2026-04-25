"""Background worker for long-running pipeline jobs.

In production this is a separate container that pops jobs from Redis and runs
the vision pipeline + SOP generator. For dev we keep it simple and process
any sessions that are in ``PENDING`` state when the worker starts.
"""
from __future__ import annotations

import time

from sqlalchemy import select

from app.api.routes.sessions import _run_session
from app.core.logging import configure_logging, get_logger
from app.db.session import SessionLocal
from app.models.session import MonitoringSession, SessionStatus

log = get_logger(__name__)


def main() -> None:
    configure_logging()
    log.info("worker.start")
    while True:
        db = SessionLocal()
        try:
            pending = db.execute(
                select(MonitoringSession)
                .where(MonitoringSession.status == SessionStatus.PENDING)
                .limit(1)
            ).scalar_one_or_none()
        finally:
            db.close()

        if pending is None:
            time.sleep(2.0)
            continue

        log.info("worker.pick", session_id=pending.id)
        try:
            _run_session(pending.id)
        except Exception as exc:  # pragma: no cover
            log.exception("worker.run_failed", session_id=pending.id, error=str(exc))
        time.sleep(0.5)


if __name__ == "__main__":
    main()
