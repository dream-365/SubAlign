"""SRT/ASS parsing with byte-preserving raw lines."""

from __future__ import annotations

import re
from pathlib import Path

from ..errors import SubtitleParseError
from .model import SubtitleCue, SubtitleDocument
from .normalize import detect_lang, normalize_text, strip_tags

_SRT_TIME_RE = re.compile(
    r"^\s*(\d{1,3}):(\d{2}):(\d{2})[,.](\d{3})\s*-->\s*"
    r"(\d{1,3}):(\d{2}):(\d{2})[,.](\d{3})(.*)$"
)
_ASS_TIME_RE = re.compile(r"^\s*(\d+):(\d{2}):(\d{2})[.:](\d{1,2})\s*$")
_ASS_DEFAULT_FORMAT = [
    "Layer", "Start", "End", "Style", "Name",
    "MarginL", "MarginR", "MarginV", "Effect", "Text",
]


def read_text(path: str | Path) -> tuple[str, str, bool]:
    data = Path(path).read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        return data.decode("utf-8-sig"), "utf-8", True
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        return data.decode("utf-16"), "utf-16", False
    for encoding in ("utf-8", "gb18030"):
        try:
            return data.decode(encoding), encoding, False
        except UnicodeDecodeError:
            continue
    raise SubtitleParseError("字幕文件编码无法识别", detail="支持 UTF-8 / UTF-8 BOM / GB18030 / UTF-16")


def parse_srt_time(hours: str, minutes: str, seconds: str, millis: str) -> float:
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000.0


def parse_ass_time(hours: str, minutes: str, seconds: str, centis: str) -> float:
    cs = int(centis.ljust(2, "0")[:2])
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + cs / 100.0


def format_srt_time(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def format_ass_time(seconds: float) -> str:
    total_cs = max(0, int(round(seconds * 100)))
    hours, rem = divmod(total_cs, 360_000)
    minutes, rem = divmod(rem, 6_000)
    secs, centis = divmod(rem, 100)
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{centis:02d}"


def _new_cue(index: int, start: float, end: float, text: str, line_pos: int,
             subtitle_format: str, settings: str = "") -> SubtitleCue:
    normalized = normalize_text(text, subtitle_format)
    return SubtitleCue(
        index=index,
        start=start,
        end=end,
        text=text,
        normalized=normalized,
        lang=detect_lang(strip_tags(text, subtitle_format)),
        anchor_text=normalized,
        line_pos=line_pos,
        settings=settings,
    )


def parse_srt(lines: list[str]) -> list[SubtitleCue]:
    cues: list[SubtitleCue] = []
    i = 0
    auto_index = 1
    while i < len(lines):
        match = _SRT_TIME_RE.match(lines[i].rstrip("\r\n"))
        if not match:
            i += 1
            continue
        start = parse_srt_time(*match.group(1, 2, 3, 4))
        end = parse_srt_time(*match.group(5, 6, 7, 8))
        settings = match.group(9).strip()
        index = auto_index
        if i > 0:
            previous = lines[i - 1].strip()
            if previous.isdigit():
                index = int(previous)
        text_lines: list[str] = []
        j = i + 1
        while j < len(lines):
            body = lines[j].rstrip("\r\n")
            if not body.strip():
                break
            if _SRT_TIME_RE.match(body):
                break
            text_lines.append(body)
            j += 1
        if not text_lines:
            raise SubtitleParseError("字幕行缺少文本", detail=f"时间码位于第 {i + 1} 行")
        cues.append(_new_cue(index, start, end, "\n".join(text_lines), i, "srt", settings))
        auto_index = max(auto_index, index) + 1
        i = j + 1 if j < len(lines) and not lines[j].strip() else j
    if not cues:
        raise SubtitleParseError("没有解析到任何字幕行")
    return cues


def _parse_ass_format(line: str) -> list[str]:
    _, _, payload = line.partition(":")
    return [part.strip() for part in payload.split(",")]


def _split_ass_fields(payload: str, count: int) -> list[str]:
    return payload.split(",", count - 1)


def parse_ass(lines: list[str]) -> tuple[list[SubtitleCue], list[str]]:
    ass_format: list[str] = []
    in_events = False
    cues: list[SubtitleCue] = []
    for pos, raw in enumerate(lines):
        body = raw.rstrip("\r\n")
        stripped = body.strip()
        if stripped.startswith("["):
            in_events = stripped.lower() == "[events]"
            continue
        if not in_events:
            continue
        if stripped.lower().startswith("format:"):
            ass_format = _parse_ass_format(body)
            continue
        if not stripped.lower().startswith("dialogue:"):
            continue
        fields = ass_format or _ASS_DEFAULT_FORMAT
        payload = body.split(":", 1)[1].lstrip()
        values = _split_ass_fields(payload, len(fields))
        if len(values) < len(fields):
            raise SubtitleParseError("ASS Dialogue 字段数量不足", detail=f"第 {pos + 1} 行")
        row = {name.lower(): value for name, value in zip(fields, values)}
        start_raw = row.get("start", "")
        end_raw = row.get("end", "")
        start_match = _ASS_TIME_RE.match(start_raw)
        end_match = _ASS_TIME_RE.match(end_raw)
        if not start_match or not end_match:
            raise SubtitleParseError("ASS 时间码格式错误", detail=f"第 {pos + 1} 行")
        start = parse_ass_time(*start_match.groups())
        end = parse_ass_time(*end_match.groups())
        text = row.get("text", "")
        cues.append(_new_cue(len(cues) + 1, start, end, text, pos, "ass"))
    if not cues:
        raise SubtitleParseError("没有解析到任何 ASS Dialogue 事件")
    return cues, ass_format or _ASS_DEFAULT_FORMAT


def parse_subtitle(path: str | Path) -> SubtitleDocument:
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix not in (".srt", ".ass", ".ssa"):
        raise SubtitleParseError("不支持的字幕扩展名", detail=suffix or "无扩展名")
    text, encoding, bom = read_text(path)
    lines = text.splitlines(keepends=True)
    if suffix == ".srt":
        cues = parse_srt(lines)
        return SubtitleDocument("srt", cues, lines, encoding, bom)
    cues, ass_format = parse_ass(lines)
    return SubtitleDocument("ass", cues, lines, encoding, bom, ass_format)
