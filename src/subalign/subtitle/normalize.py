"""Text normalization and language tagging used by matching."""

from __future__ import annotations

import re
import unicodedata

_CJK_RANGES = (
    (0x3400, 0x4DBF),
    (0x4E00, 0x9FFF),
    (0xF900, 0xFAFF),
    (0x3040, 0x30FF),
    (0xAC00, 0xD7AF),
)

_ASS_TAG_RE = re.compile(r"\{[^}]*\}")
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_BREAK_RE = re.compile(r"\\N|\\n|<br\s*/?>|\r?\n", re.IGNORECASE)


def is_cjk(ch: str) -> bool:
    code = ord(ch)
    return any(lo <= code <= hi for lo, hi in _CJK_RANGES)


def detect_lang(text: str) -> str:
    cjk = sum(1 for ch in text if is_cjk(ch))
    latin = sum(1 for ch in text if ("a" <= ch.lower() <= "z"))
    total = cjk + latin
    if total == 0:
        return "mixed"
    if cjk / total >= 0.5:
        return "zh"
    if latin / total >= 0.5:
        return "en"
    return "mixed"


def visual_lines(text: str) -> list[str]:
    return [line.strip() for line in _BREAK_RE.split(text) if line.strip()]


def strip_tags(text: str, subtitle_format: str) -> str:
    if subtitle_format == "ass":
        return _ASS_TAG_RE.sub("", text)
    return _HTML_TAG_RE.sub("", text)


def normalize_text(text: str, subtitle_format: str = "srt") -> str:
    text = strip_tags(text, subtitle_format)
    text = unicodedata.normalize("NFKC", text)
    text = _BREAK_RE.sub(" ", text)
    out: list[str] = []
    for ch in text:
        category = unicodedata.category(ch)
        if ch.isalnum() or is_cjk(ch) or category.startswith("M"):
            out.append(ch.lower() if "A" <= ch <= "Z" else ch)
        else:
            out.append(" ")
    return re.sub(r"\s+", "", "".join(out))


def pick_anchor_text(text: str, subtitle_format: str, asr_lang: str) -> str:
    """Choose the visual line(s) that match the ASR language."""
    lines = visual_lines(strip_tags(text, subtitle_format))
    if not lines:
        return ""
    if asr_lang in ("zh", "en"):
        matched = [line for line in lines if detect_lang(line) == asr_lang]
        if matched:
            return normalize_text(" ".join(matched), subtitle_format)
    return normalize_text(text, subtitle_format)
