"""Seed rich demo data and assets for capstone presentations."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import cv2
import matplotlib
import numpy as np
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.action import ActionEvent
from app.models.alert import Alert, AlertSeverity
from app.models.session import MonitoringSession, SessionStatus
from app.models.sop import SOP, SOPStatus, SOPStep
from app.models.user import User, UserRole

matplotlib.use("Agg")
import matplotlib.pyplot as plt


def video_path(name: str) -> str:
    return str(settings.video_dir / name)


@dataclass(frozen=True)
class DemoAsset:
    filename: str
    title: str
    station: str
    primary: tuple[int, int]
    secondary: tuple[int, int]
    accent: tuple[int, int]
    hotspot_centers: tuple[tuple[int, int], ...]


DEMO_ASSETS = [
    DemoAsset(
        filename="final-assembly-reference.mp4",
        title="Final Assembly Reference",
        station="Station 1",
        primary=(170, 180),
        secondary=(320, 170),
        accent=(475, 185),
        hotspot_centers=((170, 180), (315, 170), (470, 185)),
    ),
    DemoAsset(
        filename="final-assembly-run-delayed.mp4",
        title="Final Assembly Delayed Run",
        station="Station 1",
        primary=(160, 195),
        secondary=(340, 160),
        accent=(500, 210),
        hotspot_centers=((160, 195), (340, 160), (500, 210), (560, 250)),
    ),
    DemoAsset(
        filename="subassembly-reference.mp4",
        title="Sub-Assembly Reference",
        station="Station 2",
        primary=(155, 185),
        secondary=(295, 200),
        accent=(460, 170),
        hotspot_centers=((155, 185), (295, 200), (460, 170)),
    ),
    DemoAsset(
        filename="subassembly-motion-waste.mp4",
        title="Sub-Assembly Motion Waste",
        station="Station 2",
        primary=(150, 210),
        secondary=(330, 150),
        accent=(535, 225),
        hotspot_centers=((150, 210), (330, 150), (535, 225), (590, 245)),
    ),
]

ASSET_LOOKUP = {asset.filename: asset for asset in DEMO_ASSETS}

DEMO_USERS = [
    {"email": "admin@vision-sop.dev", "full_name": "Aisha Admin", "role": UserRole.ADMIN},
    {"email": "supervisor@vision-sop.dev", "full_name": "Sam Supervisor", "role": UserRole.SUPERVISOR},
    {"email": "engineer@vision-sop.dev", "full_name": "Evan Engineer", "role": UserRole.ENGINEER},
    {"email": "operator@vision-sop.dev", "full_name": "Olivia Operator", "role": UserRole.OPERATOR},
]

DEMO_SOPS = [
    {
        "title": "Final Assembly QA",
        "station": "Station 1",
        "status": SOPStatus.PUBLISHED,
        "description": "Reference SOP for the final assembly and outgoing quality gate.",
        "source_video_path": video_path("final-assembly-reference.mp4"),
        "rendered_markdown": """# Final Assembly QA

## Objective
Validate the assembled unit, confirm all electrical connections, complete the power-on check, and present a polished finished good.

## Standard sequence
1. Inspect the frame and confirm the assembly is seated correctly.
2. Verify all electrical and mechanical connections.
3. Run the power-on test and confirm indicator behavior.
4. Finish with visual polish before hand-off.

## Quality notes
- Escalate immediately if a connector is loose or if the power-on check exceeds the standard time.
- Keep tools staged on the right side to reduce walking and searching.
""",
        "steps": [
            ("inspect_frame", "Inspect Frame", 3.0, 1.0, ["gloves"]),
            ("verify_connections", "Verify Connections", 5.0, 1.5, ["gloves"]),
            ("power_on_test", "Power-On Test", 10.0, 2.0, ["gloves", "safety_glasses"]),
            ("final_polish", "Final Polish", 4.0, 1.0, ["gloves"]),
        ],
    },
    {
        "title": "Sub-Assembly Part B",
        "station": "Station 2",
        "status": SOPStatus.PUBLISHED,
        "description": "Reference SOP for aligning, fastening, and cabling the Part B module.",
        "source_video_path": video_path("subassembly-reference.mp4"),
        "rendered_markdown": """# Sub-Assembly Part B

## Objective
Assemble the Part B module in a repeatable sequence with correct alignment and fastening torque.

## Standard sequence
1. Align the mating parts using the fixture.
2. Fasten all four screws in the correct order.
3. Attach the cable and inspect the routing.

## Improvement note
- Fasten screws with the torque tool staged directly beside the jig to avoid extra motion.
""",
        "steps": [
            ("align_parts", "Align Parts", 4.0, 1.0, ["gloves"]),
            ("fasten_screws", "Fasten Screws", 6.0, 1.5, ["gloves", "safety_glasses"]),
            ("attach_cable", "Attach Cable", 3.0, 1.0, ["gloves"]),
        ],
    },
    {
        "title": "Initial Component Prep",
        "station": "Station 1",
        "status": SOPStatus.DRAFT,
        "description": "Draft preparation SOP awaiting approval after the reference capture review.",
        "source_video_path": video_path("final-assembly-reference.mp4"),
        "rendered_markdown": """# Initial Component Prep

This draft was auto-generated from a reference clip and is pending engineer review before publication.
""",
        "steps": [
            ("unpack_components", "Unpack Components", 5.0, 1.0, ["gloves"]),
            ("stage_bins", "Stage Bins", 3.0, 1.0, ["gloves"]),
        ],
    },
]

DEMO_SESSIONS = [
    {
        "key": "final-assembly-delayed",
        "source_uri": video_path("final-assembly-run-delayed.mp4"),
        "sop_title": "Final Assembly QA",
        "operator_ref": "OP-104",
        "mode": "offline",
        "status": SessionStatus.COMPLETED,
        "started_delta": timedelta(hours=5, minutes=40),
        "completed_delta": timedelta(hours=5, minutes=39, seconds=22),
        "cycle_time_s": 35.1,
        "deviation_score": 0.21,
        "summary": {
            "total_steps": 4,
            "matched_steps": 4,
            "skipped_steps": [],
            "extra_steps": ["move"],
            "target_cycle_time_s": 22.0,
            "alerts": 2,
            "ergonomics": {
                "score": 5,
                "mean_shoulder_abduction_deg": 72.4,
                "mean_elbow_flexion_deg": 141.2,
                "reach_percentile_95": 384.0,
                "hotspots": [
                    {"area": "shoulder", "message": "Frequent high shoulder reach during verification at Station 1."},
                    {"area": "reach", "message": "95th-percentile reach suggests the power-test fixture is positioned too far right."},
                ],
                "recommendations": [
                    "Move the tester 20 cm closer to reduce shoulder elevation.",
                    "Stage tools in the primary reach zone before the power-on step.",
                ],
            },
        },
        "actions": [
            (0, "idle", 0.0, 4.2, 0.88),
            (1, "inspect_frame", 4.2, 7.5, 0.96),
            (2, "move", 7.5, 9.4, 0.72),
            (3, "verify_connections", 9.4, 15.2, 0.93),
            (4, "power_on_test", 15.2, 27.0, 0.97),
            (5, "final_polish", 27.0, 31.2, 0.91),
        ],
        "alerts": [
            {"rule": "step_over_time", "severity": AlertSeverity.WARNING, "title": "Power-On Test Over Target", "message": "Power-On Test took 11.8s, which is 1.8s above the standard.", "at_s": 26.7, "acknowledged": False},
            {"rule": "excess_motion", "severity": AlertSeverity.INFO, "title": "Extra Walking Detected", "message": "The operator walked away from the tool zone before verification.", "at_s": 8.4, "acknowledged": True},
        ],
    },
    {
        "key": "final-assembly-reference-run",
        "source_uri": video_path("final-assembly-reference.mp4"),
        "sop_title": "Final Assembly QA",
        "operator_ref": "OP-115",
        "mode": "offline",
        "status": SessionStatus.COMPLETED,
        "started_delta": timedelta(hours=3, minutes=12),
        "completed_delta": timedelta(hours=3, minutes=11, seconds=27),
        "cycle_time_s": 27.6,
        "deviation_score": 0.08,
        "summary": {
            "total_steps": 4,
            "matched_steps": 4,
            "skipped_steps": [],
            "extra_steps": [],
            "target_cycle_time_s": 22.0,
            "alerts": 1,
            "ergonomics": {
                "score": 2,
                "mean_shoulder_abduction_deg": 42.1,
                "mean_elbow_flexion_deg": 117.5,
                "reach_percentile_95": 248.0,
                "hotspots": [{"area": "reach", "message": "Reference run stays mostly inside the preferred reach zone."}],
                "recommendations": ["Use this run as the golden-batch reference for trainees."],
            },
        },
        "actions": [
            (0, "inspect_frame", 0.0, 2.9, 0.98),
            (1, "verify_connections", 2.9, 7.8, 0.94),
            (2, "power_on_test", 7.8, 18.4, 0.98),
            (3, "final_polish", 18.4, 21.9, 0.9),
        ],
        "alerts": [
            {"rule": "step_over_time", "severity": AlertSeverity.INFO, "title": "Power-On Test Slightly High", "message": "Power-On Test is trending above the ideal target but still acceptable.", "at_s": 18.2, "acknowledged": False},
        ],
    },
    {
        "key": "subassembly-motion-waste",
        "source_uri": video_path("subassembly-motion-waste.mp4"),
        "sop_title": "Sub-Assembly Part B",
        "operator_ref": "OP-208",
        "mode": "offline",
        "status": SessionStatus.COMPLETED,
        "started_delta": timedelta(days=1, hours=2),
        "completed_delta": timedelta(days=1, hours=1, minutes=59, seconds=40),
        "cycle_time_s": 18.4,
        "deviation_score": 0.33,
        "summary": {
            "total_steps": 3,
            "matched_steps": 3,
            "skipped_steps": [],
            "extra_steps": ["move"],
            "target_cycle_time_s": 13.0,
            "alerts": 2,
            "ergonomics": {
                "score": 6,
                "mean_shoulder_abduction_deg": 81.0,
                "mean_elbow_flexion_deg": 149.4,
                "reach_percentile_95": 410.0,
                "hotspots": [
                    {"area": "shoulder", "message": "Operator repeatedly reaches across the bench for the screw tray."},
                    {"area": "reach", "message": "Right-side hotspot indicates the cable bin is outside the neutral work envelope."},
                ],
                "recommendations": [
                    "Move the screw tray beside the fixture to cut transport motion.",
                    "Raise the cable bin to elbow height to reduce reach distance.",
                ],
            },
        },
        "actions": [
            (0, "idle", 0.0, 1.4, 0.83),
            (1, "align_parts", 1.4, 5.7, 0.95),
            (2, "move", 5.7, 7.5, 0.74),
            (3, "fasten_screws", 7.5, 15.9, 0.96),
            (4, "attach_cable", 15.9, 19.1, 0.92),
        ],
        "alerts": [
            {"rule": "step_over_time", "severity": AlertSeverity.WARNING, "title": "Fastening Delay", "message": "Fasten Screws exceeded target by 2.4s. Check torque tool staging.", "at_s": 15.7, "acknowledged": False},
            {"rule": "layout_motion", "severity": AlertSeverity.WARNING, "title": "Layout Motion Waste", "message": "Repeated side-step motion suggests the screw tray is positioned too far away.", "at_s": 6.8, "acknowledged": True},
        ],
    },
    {
        "key": "subassembly-reference-run",
        "source_uri": video_path("subassembly-reference.mp4"),
        "sop_title": "Sub-Assembly Part B",
        "operator_ref": "OP-231",
        "mode": "offline",
        "status": SessionStatus.COMPLETED,
        "started_delta": timedelta(days=2, hours=4),
        "completed_delta": timedelta(days=2, hours=3, minutes=59, seconds=48),
        "cycle_time_s": 12.6,
        "deviation_score": 0.04,
        "summary": {
            "total_steps": 3,
            "matched_steps": 3,
            "skipped_steps": [],
            "extra_steps": [],
            "target_cycle_time_s": 13.0,
            "alerts": 0,
            "ergonomics": {
                "score": 2,
                "mean_shoulder_abduction_deg": 38.7,
                "mean_elbow_flexion_deg": 112.4,
                "reach_percentile_95": 224.0,
                "hotspots": [{"area": "reach", "message": "Reference sub-assembly run remains inside the preferred reach corridor."}],
                "recommendations": ["Use this heatmap as the optimized workstation target layout."],
            },
        },
        "actions": [
            (0, "align_parts", 0.0, 3.8, 0.97),
            (1, "fasten_screws", 3.8, 10.0, 0.96),
            (2, "attach_cable", 10.0, 12.8, 0.95),
        ],
        "alerts": [],
    },
]


def ensure_demo_data(db: Session) -> dict[str, int]:
    _ensure_demo_assets()
    _clear_old_demo_data(db)
    users = _upsert_users(db)
    sops = _upsert_sops(db)
    sessions = _upsert_sessions(db)
    db.commit()
    return {"users": users, "sops": sops, "sessions": sessions}


def seed_demo_if_needed() -> bool:
    db = SessionLocal()
    try:
        ensure_demo_data(db)
        return True
    except SQLAlchemyError:
        db.rollback()
        return False
    finally:
        db.close()


def _ensure_demo_assets() -> None:
    settings.ensure_dirs()
    for asset in DEMO_ASSETS:
        target = settings.video_dir / asset.filename
        if not target.exists():
            _create_demo_video(target, asset)
        heatmap_target = settings.heatmap_dir / f"{target.stem}.png"
        if not heatmap_target.exists():
            _create_demo_heatmap(heatmap_target, asset)


def _create_demo_video(path: Path, asset: DemoAsset) -> None:
    width, height, fps, total_frames = 640, 360, 12, 120
    path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))

    points = [asset.primary, asset.secondary, asset.accent, asset.secondary, asset.primary]
    segment = total_frames // (len(points) - 1)

    for frame_idx in range(total_frames):
        frame = np.full((height, width, 3), (244, 246, 250), dtype=np.uint8)
        cv2.rectangle(frame, (35, 90), (605, 310), (230, 235, 240), -1)
        cv2.rectangle(frame, (80, 220), (560, 260), (180, 187, 198), -1)
        cv2.rectangle(frame, (110, 120), (190, 205), (59, 130, 246), -1)
        cv2.rectangle(frame, (270, 112), (350, 205), (99, 102, 241), -1)
        cv2.rectangle(frame, (455, 132), (545, 210), (249, 115, 22), -1)
        cv2.putText(frame, asset.title, (32, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (20, 32, 58), 2)
        cv2.putText(frame, asset.station, (32, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (71, 85, 105), 2)

        seg_idx = min(frame_idx // segment, len(points) - 2)
        local_t = (frame_idx % segment) / max(1, segment - 1)
        start = np.array(points[seg_idx], dtype=float)
        end = np.array(points[seg_idx + 1], dtype=float)
        center = (start + (end - start) * local_t).astype(int)
        _draw_operator(frame, tuple(center))
        writer.write(frame)

    writer.release()


def _draw_operator(frame: np.ndarray, center: tuple[int, int]) -> None:
    x, y = center
    body = (31, 41, 55)
    accent = (245, 158, 11)
    cv2.circle(frame, (x, y - 38), 14, accent, -1)
    cv2.line(frame, (x, y - 22), (x, y + 26), body, 4)
    cv2.line(frame, (x, y - 6), (x - 24, y + 10), body, 4)
    cv2.line(frame, (x, y - 6), (x + 26, y + 6), body, 4)
    cv2.line(frame, (x, y + 26), (x - 18, y + 58), body, 4)
    cv2.line(frame, (x, y + 26), (x + 18, y + 58), body, 4)


def _create_demo_heatmap(path: Path, asset: DemoAsset) -> None:
    width, height = 640, 360
    canvas = np.zeros((height, width), dtype=float)
    yy, xx = np.mgrid[0:height, 0:width]
    for cx, cy in asset.hotspot_centers:
        canvas += np.exp(-(((xx - cx) ** 2) + ((yy - cy) ** 2)) / (2 * (34 ** 2)))
    canvas = canvas / max(canvas.max(), 1e-6)

    fig, ax = plt.subplots(figsize=(6.4, 3.6), dpi=100)
    ax.imshow(canvas, cmap="magma", interpolation="bilinear")
    ax.set_axis_off()
    ax.set_title(f"Ergonomic Heatmap - {asset.title}", fontsize=10)
    fig.tight_layout(pad=0)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", pad_inches=0)
    plt.close(fig)


def _clear_old_demo_data(db: Session) -> None:
    for session in db.execute(select(MonitoringSession).where(MonitoringSession.operator_ref.like("OP-%"))).scalars().all():
        db.delete(session)

    for title in [item["title"] for item in DEMO_SOPS]:
        for sop in db.execute(select(SOP).where(SOP.title == title)).scalars().all():
            db.delete(sop)

    for email in [item["email"] for item in DEMO_USERS]:
        for user in db.execute(select(User).where(User.email == email)).scalars().all():
            db.delete(user)

    db.flush()


def _upsert_users(db: Session) -> int:
    count = 0
    for spec in DEMO_USERS:
        user = User(
            email=spec["email"],
            full_name=spec["full_name"],
            hashed_password=f"demo-disabled-{spec['role'].value}",
            role=spec["role"],
            is_active=True,
        )
        db.add(user)
        count += 1
    db.flush()
    return count


def _upsert_sops(db: Session) -> int:
    count = 0
    for spec in DEMO_SOPS:
        sop = SOP(
            title=spec["title"],
            station=spec["station"],
            status=spec["status"],
            description=spec["description"],
            source_video_path=spec["source_video_path"],
            rendered_markdown=spec["rendered_markdown"],
            target_cycle_time_s=round(sum(step[2] for step in spec["steps"]), 1),
            generation_metadata={"seeded": True, "demo": True, "note": "Preloaded capstone dataset"},
        )
        for index, (label, title, duration_s, tolerance_s, required_ppe) in enumerate(spec["steps"]):
            sop.steps.append(
                SOPStep(
                    step_index=index,
                    action_label=label,
                    title=title,
                    instruction=f"Perform {title.lower()} according to the reference motion.",
                    target_duration_s=duration_s,
                    tolerance_s=tolerance_s,
                    required_ppe=required_ppe,
                )
            )
        db.add(sop)
        count += 1
    db.flush()
    return count


def _upsert_sessions(db: Session) -> int:
    count = 0
    now = datetime.now(timezone.utc)
    sops_by_title = {sop.title: sop for sop in db.execute(select(SOP)).scalars().all()}

    for spec in DEMO_SESSIONS:
        session = MonitoringSession(
            sop_id=sops_by_title[spec["sop_title"]].id,
            operator_ref=spec["operator_ref"],
            source_uri=spec["source_uri"],
            mode=spec["mode"],
            status=spec["status"],
            started_at=now - spec["started_delta"],
            completed_at=now - spec["completed_delta"],
            cycle_time_s=spec["cycle_time_s"],
            deviation_score=spec["deviation_score"],
            summary={**spec["summary"], "demo_key": spec["key"]},
        )
        for step_index, label, start_s, end_s, confidence in spec["actions"]:
            session.actions.append(
                ActionEvent(
                    step_index=step_index,
                    label=label,
                    start_s=start_s,
                    end_s=end_s,
                    confidence=confidence,
                    metadata_blob={"seeded": True},
                )
            )
        for alert in spec["alerts"]:
            session.alerts.append(
                Alert(
                    rule=alert["rule"],
                    severity=alert["severity"],
                    title=alert["title"],
                    message=alert["message"],
                    at_s=alert["at_s"],
                    acknowledged=alert["acknowledged"],
                    evidence={"seeded": True},
                )
            )
        db.add(session)
        count += 1

    db.flush()
    return count


def main() -> None:
    db = SessionLocal()
    try:
        result = ensure_demo_data(db)
        print(
            "Seed complete: "
            f"{result['users']} users created, "
            f"{result['sops']} SOPs created, "
            f"{result['sessions']} sessions created."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()

