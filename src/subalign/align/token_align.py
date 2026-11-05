"""Character-level alignment of anchor text against the ASR token stream."""

from __future__ import annotations

import bisect
import difflib

from ..subtitle.model import Anchor, AsrToken, BilingualGroup, SubtitleDocument
from ..subtitle.normalize import normalize_text


def _window(tokens: list[AsrToken], start: float, end: float) -> list[AsrToken]:
    starts = [token.start for token in tokens]
    lo = max(0, bisect.bisect_left(starts, start) - 1)
    hi = bisect.bisect_right(starts, end) + 1
    return tokens[lo:hi]


def _align_window(cue_text: str, window: list[AsrToken]) -> tuple[float, float, float] | None:
    if not cue_text or not window:
        return None
    chars: list[str] = []
    char_to_token: list[int] = []
    for idx, token in enumerate(window):
        normalized = normalize_text(token.text, "srt")
        for ch in normalized:
            chars.append(ch)
            char_to_token.append(idx)
    haystack = "".join(chars)
    if not haystack:
        return None
    matcher = difflib.SequenceMatcher(None, cue_text, haystack, autojunk=False)
    blocks = [block for block in matcher.get_matching_blocks() if block.size > 0]
    if not blocks:
        return None
    matched = sum(block.size for block in blocks)
    ratio = matched / len(cue_text)
    first = blocks[0]
    last = blocks[-1]
    first_token = window[char_to_token[first.b]]
    last_token = window[char_to_token[last.b + last.size - 1]]
    if last_token.end <= first_token.start:
        return None
    return ratio, first_token.start, last_token.end


def _distance(cue_start: float, cue_end: float, audio_start: float, audio_end: float) -> float:
    if audio_start <= cue_start and audio_end >= cue_end:
        return 0.0
    return min(abs(audio_start - cue_start), abs(audio_end - cue_end))


def align(doc: SubtitleDocument, groups: list[BilingualGroup],
          tokens: list[AsrToken], max_offset: float = 60.0) -> list[Anchor]:
    if not tokens:
        return []
    anchor_indices = {group.anchor_cue_index for group in groups}
    anchors: list[Anchor] = []
    for cue in doc.cues:
        if cue.group_id and cue.index not in anchor_indices:
            continue
        cue_text = cue.anchor_text or cue.normalized
        if not cue_text:
            continue
        local = _align_window(cue_text, _window(tokens, cue.start - 15.0, cue.end + 15.0))
        wide = _align_window(cue_text, _window(tokens, cue.start - max_offset, cue.end + max_offset))
        if local and local[0] >= 0.8:
            ratio, audio_start, audio_end = local
        elif local and wide:
            ratio, audio_start, audio_end = max(
                [local, wide],
                key=lambda item: (item[0], -_distance(cue.start, cue.end, item[1], item[2])),
            )
        elif local or wide:
            ratio, audio_start, audio_end = local or wide  # type: ignore[misc]
        else:
            continue
        if ratio < 0.35:
            continue
        confidence = "high" if ratio >= 0.8 else ("medium" if ratio >= 0.6 else "low")
        anchors.append(
            Anchor(
                cue_index=cue.index,
                group_id=cue.group_id,
                audio_start=audio_start,
                audio_end=audio_end,
                matched_ratio=ratio,
                confidence=confidence,
            )
        )
    return anchors
