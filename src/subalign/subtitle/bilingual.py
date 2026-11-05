"""Bilingual grouping and anchor-line selection."""

from __future__ import annotations

from .model import BilingualGroup, SubtitleDocument
from .normalize import pick_anchor_text


def _overlap_ratio(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    overlap = max(0.0, min(a_end, b_end) - max(a_start, b_start))
    shortest = min(a_end - a_start, b_end - b_start)
    if shortest <= 0:
        return 0.0
    return overlap / shortest


def group_bilingual(doc: SubtitleDocument, asr_lang: str) -> list[BilingualGroup]:
    for cue in doc.cues:
        cue.group_id = 0
        cue.anchor_text = pick_anchor_text(cue.text, doc.format, asr_lang)

    groups: list[BilingualGroup] = []
    used: set[int] = set()
    cues = sorted(doc.cues, key=lambda cue: (cue.start, cue.index))

    for pos, first in enumerate(cues):
        if first.index in used or first.lang not in ("zh", "en"):
            continue
        best: tuple[float, object] | None = None
        for second in cues[pos + 1:]:
            if second.start > first.end + 0.001:
                break
            if second.index in used or second.lang not in ("zh", "en"):
                continue
            if second.lang == first.lang:
                continue
            ratio = _overlap_ratio(first.start, first.end, second.start, second.end)
            if ratio < 0.8:
                continue
            if best is None or ratio > best[0]:
                best = (ratio, second)
        if best is None:
            continue
        second = best[1]
        if asr_lang == first.lang:
            anchor = first
        elif asr_lang == second.lang:
            anchor = second
        else:
            anchor = first if len(first.normalized) >= len(second.normalized) else second
        group_id = len(groups) + 1
        first.group_id = group_id
        second.group_id = group_id
        used.update({first.index, second.index})
        groups.append(
            BilingualGroup(
                group_id=group_id,
                cue_indices=[first.index, second.index],
                anchor_cue_index=anchor.index,
                anchor_lang=anchor.lang,
            )
        )
    return groups
