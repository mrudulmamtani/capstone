"""Temporal Action Localisation (TAL).

Given a stream of per-frame :class:`ActionScore` objects, collapse them into a
sequence of :class:`ActionSegment` objects — one per contiguous run of the
same dominant label. Brief noise bursts are smoothed away so the generated
SOP doesn't contain dozens of 100ms "reach" flickers.

This implementation is intentionally simple and auditable: a rolling majority
vote plus a minimum-segment-duration filter. It runs in O(n) time and can be
called in streaming mode on a live feed or batch mode on a whole video.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Iterator

from app.vision.types import ActionScore


@dataclass
class ActionSegment:
    label: str
    start_s: float
    end_s: float
    confidence: float
    frame_count: int = 0
    per_frame_labels: list[str] = field(default_factory=list)

    @property
    def duration_s(self) -> float:
        return max(0.0, self.end_s - self.start_s)


class TemporalActionLocalizer:
    def __init__(
        self,
        window_size: int = 9,
        min_segment_s: float = 0.6,
        idle_label: str = "idle",
    ) -> None:
        if window_size < 1 or window_size % 2 == 0:
            raise ValueError("window_size must be a positive odd integer")
        self.window_size = window_size
        self.min_segment_s = min_segment_s
        self.idle_label = idle_label

    # -------------------------------------------------------------- batch
    def localize(self, scores: Iterable[ActionScore]) -> list[ActionSegment]:
        labels = list(self._smooth_labels(scores))
        if not labels:
            return []

        segments = self._group_into_segments(labels)
        segments = self._drop_short(segments)
        segments = self._merge_adjacent_same(segments)
        # re-index so frame_count is correct after merges
        return segments

    # ------------------------------------------------------------- helper
    def _smooth_labels(
        self, scores: Iterable[ActionScore]
    ) -> Iterator[tuple[int, float, str, float]]:
        """Yield (frame_index, timestamp_s, label, confidence) with majority smoothing."""
        buffer: list[ActionScore] = []
        half = self.window_size // 2

        scores_list = list(scores)
        for i, s in enumerate(scores_list):
            lo = max(0, i - half)
            hi = min(len(scores_list), i + half + 1)
            window = scores_list[lo:hi]
            vote = Counter(w.top_label for w in window)
            best_label, _ = vote.most_common(1)[0]
            best_conf = sum(w.scores.get(best_label, 0.0) for w in window) / max(1, len(window))
            yield s.frame_index, s.timestamp_s, best_label, best_conf
        _ = buffer  # silence linter

    def _group_into_segments(
        self, items: list[tuple[int, float, str, float]]
    ) -> list[ActionSegment]:
        segments: list[ActionSegment] = []
        if not items:
            return segments

        _, t0, current, conf = items[0]
        start = t0
        confs = [conf]
        labels = [current]
        prev_t = t0

        for _, t, label, c in items[1:]:
            if label != current:
                segments.append(
                    ActionSegment(
                        label=current,
                        start_s=start,
                        end_s=prev_t,
                        confidence=sum(confs) / len(confs),
                        frame_count=len(confs),
                        per_frame_labels=labels,
                    )
                )
                current = label
                start = t
                confs = [c]
                labels = [label]
            else:
                confs.append(c)
                labels.append(label)
            prev_t = t

        segments.append(
            ActionSegment(
                label=current,
                start_s=start,
                end_s=prev_t,
                confidence=sum(confs) / len(confs),
                frame_count=len(confs),
                per_frame_labels=labels,
            )
        )
        return segments

    def _drop_short(self, segs: list[ActionSegment]) -> list[ActionSegment]:
        if not segs:
            return segs
        keep: list[ActionSegment] = []
        for s in segs:
            if s.duration_s >= self.min_segment_s or s.label == self.idle_label:
                keep.append(s)
            else:
                # Absorb into previous segment if possible.
                if keep:
                    prev = keep[-1]
                    prev.end_s = s.end_s
                    prev.frame_count += s.frame_count
        return keep

    @staticmethod
    def _merge_adjacent_same(segs: list[ActionSegment]) -> list[ActionSegment]:
        if not segs:
            return segs
        merged: list[ActionSegment] = [segs[0]]
        for s in segs[1:]:
            last = merged[-1]
            if s.label == last.label:
                last.end_s = s.end_s
                last.frame_count += s.frame_count
                last.confidence = (last.confidence + s.confidence) / 2
            else:
                merged.append(s)
        return merged
