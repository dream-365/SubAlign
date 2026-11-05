"""Constant / linear / piecewise-constant offset model selection."""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass

from ..subtitle.model import (
    Anchor,
    BilingualGroup,
    CueAdjustment,
    OffsetModel,
    SubtitleDocument,
)

MIN_SEGMENT = 5
RMSE_IMPROVEMENT = 0.03


@dataclass
class Point:
    t: float
    residual: float
    cue_index: int


def _rmse(residuals: list[float]) -> float:
    if not residuals:
        return 0.0
    return math.sqrt(sum(value * value for value in residuals) / len(residuals))


def _linear_fit(points: list[Point]) -> tuple[float, float, float]:
    if len(points) < 2:
        offset = statistics.median(p.residual for p in points) if points else 0.0
        return offset, 0.0, _rmse([p.residual - offset for p in points])
    kept = list(points)
    for _ in range(3):
        n = len(kept)
        mean_t = sum(p.t for p in kept) / n
        mean_r = sum(p.residual for p in kept) / n
        denom = sum((p.t - mean_t) ** 2 for p in kept)
        if denom == 0:
            return mean_r, 0.0, _rmse([p.residual - mean_r for p in kept])
        slope = sum((p.t - mean_t) * (p.residual - mean_r) for p in kept) / denom
        intercept = mean_r - slope * mean_t
        residuals = [p.residual - (intercept + slope * p.t) for p in kept]
        mad = statistics.median(abs(value - statistics.median(residuals)) for value in residuals)
        if mad == 0:
            break
        limit = 3.0 * 1.4826 * mad
        filtered = [p for p, value in zip(kept, residuals) if abs(value) <= limit]
        if len(filtered) < max(3, len(kept) // 3) or len(filtered) == len(kept):
            break
        kept = filtered
    n = len(kept)
    mean_t = sum(p.t for p in kept) / n
    mean_r = sum(p.residual for p in kept) / n
    denom = sum((p.t - mean_t) ** 2 for p in kept)
    slope = 0.0 if denom == 0 else sum((p.t - mean_t) * (p.residual - mean_r) for p in kept) / denom
    intercept = mean_r - slope * mean_t
    residuals = [p.residual - (intercept + slope * p.t) for p in kept]
    return intercept, slope, _rmse(residuals)


def _slope_significant(points: list[Point], slope: float) -> bool:
    if len(points) < 3 or slope == 0:
        return False
    intercept, _, _ = _linear_fit(points)
    residuals = [p.residual - (intercept + slope * p.t) for p in points]
    variance = sum(value * value for value in residuals) / max(1, len(points) - 2)
    mean_t = sum(p.t for p in points) / len(points)
    denom = sum((p.t - mean_t) ** 2 for p in points)
    if denom == 0:
        return False
    standard_error = math.sqrt(variance / denom)
    if standard_error == 0:
        return True
    return abs(slope / standard_error) >= 2.0


def _prefix_sums(points: list[Point]) -> tuple[list[float], list[float]]:
    sums = [0.0]
    squares = [0.0]
    for point in points:
        sums.append(sums[-1] + point.residual)
        squares.append(squares[-1] + point.residual * point.residual)
    return sums, squares


def _sse(sums: list[float], squares: list[float], i: int, j: int) -> float:
    count = j - i
    if count <= 0:
        return 0.0
    total = sums[j] - sums[i]
    total_sq = squares[j] - squares[i]
    return max(0.0, total_sq - total * total / count)


def _piecewise(points: list[Point]) -> OffsetModel | None:
    n = len(points)
    if n < MIN_SEGMENT * 2:
        return None
    sums, squares = _prefix_sums(points)
    penalty = n * (RMSE_IMPROVEMENT ** 2)
    inf = float("inf")
    dp = [inf] * (n + 1)
    previous = [-1] * (n + 1)
    dp[0] = 0.0
    for j in range(MIN_SEGMENT, n + 1):
        best = inf
        best_i = -1
        for i in range(0, j - MIN_SEGMENT + 1):
            if dp[i] == inf:
                continue
            cost = dp[i] + _sse(sums, squares, i, j) + penalty
            if cost < best:
                best = cost
                best_i = i
        dp[j] = best
        previous[j] = best_i
    if previous[n] < 0:
        return None
    segments: list[tuple[int, int]] = []
    cursor = n
    while cursor > 0:
        start = previous[cursor]
        if start < 0:
            break
        segments.append((start, cursor))
        cursor = start
    segments.reverse()
    if len(segments) < 2:
        return None
    offsets = []
    residuals: list[float] = []
    breakpoints: list[float] = []
    for seg_index, (start, end) in enumerate(segments):
        segment_points = points[start:end]
        offset = statistics.median(point.residual for point in segment_points)
        offsets.append(offset)
        residuals.extend(point.residual - offset for point in segment_points)
        if seg_index > 0:
            breakpoints.append(points[start].t)
    return OffsetModel(
        kind="piecewise",
        intercept=0.0,
        slope=0.0,
        breakpoints=breakpoints,
        rmse=_rmse(residuals),
        segment_offsets=offsets,
    )


def _nearest_cue_index(points: list[Point], t: float) -> int:
    return min(points, key=lambda point: abs(point.t - t)).cue_index


def _breakpoints_stable(points: list[Point], model: OffsetModel) -> bool:
    if len(points) < 20 or not model.breakpoints:
        return True
    cut = max(MIN_SEGMENT * 2, int(len(points) * 0.8))
    subsets = [points[:cut], points[-cut:]]
    for subset in subsets:
        alternative = _piecewise(subset)
        if alternative is None:
            return False
        for breakpoint in model.breakpoints:
            source = _nearest_cue_index(points, breakpoint)
            target = _nearest_cue_index(subset, breakpoint)
            nearest = min(alternative.breakpoints, key=lambda value: abs(value - breakpoint), default=None)
            if nearest is None:
                return False
            target = _nearest_cue_index(subset, nearest)
            if abs(source - target) > 2:
                return False
    return True


def _local_medians(points: list[Point], window: int = 9) -> list[float]:
    count = len(points)
    result = []
    for index in range(count):
        low = max(0, index - window // 2)
        high = min(count, index + window // 2 + 1)
        result.append(statistics.median(point.residual for point in points[low:high]))
    return result


def _robust_inliers(points: list[Point], threshold: float = 1.5) -> list[Point]:
    if len(points) < 3:
        return points
    local = _local_medians(points)
    kept = [
        point for point, value in zip(points, local)
        if abs(point.residual - value) <= threshold
    ]
    if len(kept) < max(3, len(points) // 3):
        return points
    return kept


def _robust_piecewise(points: list[Point]) -> OffsetModel | None:
    """Median-of-neighbours segmentation; resistant to isolated bad anchors."""
    kept = _robust_inliers(points)
    if len(kept) < 10:
        return None
    local = _local_medians(kept)
    starts = [0]
    current = statistics.median(local[:3])
    for index in range(1, len(kept)):
        if abs(local[index] - current) <= 1.0:
            continue
        tail = local[index:min(len(kept), index + 3)]
        if sum(1 for value in tail if abs(value - local[index]) < 0.6) < min(2, len(tail)):
            continue
        if index - starts[-1] < 3:
            continue
        starts.append(index)
        current = local[index]
    starts.append(len(kept))

    segments: list[list] = []
    for start, end in zip(starts, starts[1:]):
        offset = statistics.median(point.residual for point in kept[start:end])
        segments.append([start, end, offset])

    merged: list[list] = []
    for start, end, offset in segments:
        if merged and abs(merged[-1][2] - offset) < 0.6:
            merged[-1][1] = end
            merged[-1][2] = statistics.median(
                point.residual for point in kept[merged[-1][0]:end]
            )
        else:
            merged.append([start, end, offset])

    changed = True
    while changed and len(merged) > 1:
        changed = False
        for index, (start, end, offset) in enumerate(merged):
            if end - start >= 3:
                continue
            neighbours = [j for j in (index - 1, index + 1) if 0 <= j < len(merged)]
            nearest = min(neighbours, key=lambda j: abs(merged[j][2] - offset))
            low, high = min(index, nearest), max(index, nearest)
            new_start, new_end = merged[low][0], merged[high][1]
            merged[low:high + 1] = [[
                new_start,
                new_end,
                statistics.median(point.residual for point in kept[new_start:new_end]),
            ]]
            changed = True
            break

    if len(merged) < 2:
        return None
    residuals: list[float] = []
    for start, end, offset in merged:
        residuals.extend(point.residual - offset for point in kept[start:end])
    return OffsetModel(
        kind="piecewise",
        breakpoints=[kept[start].t for start, end, offset in merged[1:]],
        rmse=_rmse(residuals),
        segment_offsets=[offset for start, end, offset in merged],
    )


def select_model(anchors: list[Anchor], cues: list) -> tuple[OffsetModel, bool, list[str]]:
    warnings: list[str] = []
    high = [anchor for anchor in anchors if anchor.confidence == "high"]
    if not high:
        return OffsetModel(kind="constant", intercept=0.0, rmse=0.0), False, ["WARN_LOW_MATCH"]
    cue_map = {cue.index: cue for cue in cues}
    points = []
    for anchor in high:
        cue = cue_map.get(anchor.cue_index)
        if cue is None:
            continue
        points.append(Point(cue.start, anchor.audio_start - cue.start, cue.index))
    points.sort(key=lambda point: point.t)
    if not points:
        return OffsetModel(kind="constant", intercept=0.0, rmse=0.0), False, ["WARN_LOW_MATCH"]

    constant_offset = statistics.median(point.residual for point in points)
    constant_rmse = _rmse([point.residual - constant_offset for point in points])
    constant = OffsetModel(kind="constant", intercept=constant_offset, rmse=constant_rmse,
                           segment_offsets=[constant_offset])
    if len(points) < 3:
        return constant, False, warnings

    intercept, slope, linear_rmse = _linear_fit(points)
    linear = OffsetModel(kind="linear", intercept=intercept, slope=slope, rmse=linear_rmse)
    best = constant
    if linear_rmse <= constant_rmse - RMSE_IMPROVEMENT:
        best = linear

    robust = _robust_piecewise(points)
    if robust and robust.rmse <= best.rmse - RMSE_IMPROVEMENT:
        best = robust
    return best, False, warnings


def apply_model(doc: SubtitleDocument, model: OffsetModel, anchors: list[Anchor],
                groups: list[BilingualGroup]) -> tuple[list[CueAdjustment], float, list[str]]:
    anchor_by_cue = {
        anchor.cue_index: anchor for anchor in anchors
        if anchor.confidence in ("high", "medium")
    }
    group_anchor = {group.group_id: group.anchor_cue_index for group in groups}
    adjustments: list[CueAdjustment] = []
    warnings: list[str] = []
    covered = 0

    for cue in doc.cues:
        anchor = anchor_by_cue.get(cue.index)
        delta = model.predict(cue.start)
        if cue.group_id:
            anchor_index = group_anchor.get(cue.group_id)
            group_anchor_obj = anchor_by_cue.get(anchor_index) if anchor_index is not None else None
            if group_anchor_obj is not None:
                confidence = group_anchor_obj.confidence
                anchor_lang = cue.lang if cue.index == anchor_index else "none"
                if group_anchor_obj.confidence == "high":
                    covered += 1
            else:
                confidence = "low"
                anchor_lang = "none"
        elif anchor is not None:
            confidence = anchor.confidence
            anchor_lang = cue.lang
            if anchor.confidence == "high":
                covered += 1
        else:
            confidence = "low"
            anchor_lang = "none"

        requested_start = cue.start + delta
        duration = max(0.001, cue.end - cue.start)
        if requested_start < 0:
            final_start = 0.0
            final_end = final_start + duration
            warnings.append(
                f"WARN_CLAMPED: cue {cue.index} requested_start={requested_start:.3f}"
            )
        else:
            final_start = requested_start
            final_end = max(final_start + 0.001, cue.end + delta)
        segment_id = 0
        if model.kind == "piecewise":
            segment_id = sum(1 for point in model.breakpoints if cue.start >= point)
        adjustments.append(
            CueAdjustment(
                cue_index=cue.index,
                delta_start=final_start - cue.start,
                delta_end=final_end - cue.end,
                final_start=final_start,
                final_end=final_end,
                confidence=confidence,
                segment_id=segment_id,
                group_id=cue.group_id,
                anchor_lang=anchor_lang,
            )
        )
    coverage = covered / len(doc.cues) if doc.cues else 0.0
    return adjustments, coverage, warnings
