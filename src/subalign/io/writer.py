"""Atomic SRT/ASS writing that preserves every non-timing byte."""

from __future__ import annotations

import json
import os
import re
import tempfile
from pathlib import Path

from ..errors import OutputExists, OutputWriteError
from ..subtitle.model import CueAdjustment, SubtitleDocument
from ..subtitle.parser import format_ass_time, format_srt_time

_SRT_TIME_RE = re.compile(
    r"(\d{1,3}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{1,3}:\d{2}:\d{2}[,.]\d{3})"
)


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        if os.path.exists(temp_name):
            os.unlink(temp_name)
        raise


def _rewrite_srt_line(line: str, start: float, end: float) -> str:
    ending = line[len(line.rstrip("\r\n")):]
    body = line[:len(line) - len(ending)]
    match = _SRT_TIME_RE.search(body)
    if match is None:
        return line
    body = (
        body[:match.start(1)] + format_srt_time(start)
        + body[match.end(1):match.start(2)] + format_srt_time(end)
        + body[match.end(2):]
    )
    return body + ending


def _with_padding(original: str, value: str) -> str:
    leading = original[:len(original) - len(original.lstrip())]
    trailing = original[len(original.rstrip()):]
    return leading + value + trailing


def _rewrite_ass_line(line: str, ass_format: list[str], start: float, end: float) -> str:
    ending = line[len(line.rstrip("\r\n")):]
    body = line[:len(line) - len(ending)]
    head, separator, payload = body.partition(":")
    leading = payload[:len(payload) - len(payload.lstrip())]
    values = payload.lstrip().split(",", len(ass_format) - 1)
    if len(values) < len(ass_format):
        raise OutputWriteError("ASS Dialogue 字段数量不足", detail=head)
    for pos, name in enumerate(ass_format):
        if name.lower() == "start":
            values[pos] = _with_padding(values[pos], format_ass_time(start))
        elif name.lower() == "end":
            values[pos] = _with_padding(values[pos], format_ass_time(end))
    return head + separator + leading + ",".join(values) + ending


def write_subtitle(doc: SubtitleDocument, adjustments: list[CueAdjustment],
                   out: str | Path, force: bool = False) -> int:
    out = Path(out)
    if out.exists() and not force:
        raise OutputExists("输出文件已存在", detail=str(out))
    adjustment_by_index = {item.cue_index: item for item in adjustments}
    lines = list(doc.raw_lines)
    for cue in doc.cues:
        adjustment = adjustment_by_index.get(cue.index)
        if adjustment is None or cue.line_pos < 0 or cue.line_pos >= len(lines):
            continue
        if doc.format == "ass":
            lines[cue.line_pos] = _rewrite_ass_line(
                lines[cue.line_pos], doc.ass_format, adjustment.final_start, adjustment.final_end
            )
        else:
            lines[cue.line_pos] = _rewrite_srt_line(
                lines[cue.line_pos], adjustment.final_start, adjustment.final_end
            )
    text = "".join(lines)
    encoding = "utf-8-sig" if doc.bom else doc.encoding
    try:
        data = text.encode(encoding)
    except UnicodeEncodeError as exc:
        raise OutputWriteError("字幕无法按原编码写回", detail=str(exc)) from exc
    try:
        _atomic_write(out, data)
    except OSError as exc:
        raise OutputWriteError("写入输出字幕失败", detail=str(exc)) from exc
    return len(data)


def write_report(report: dict, path: str | Path) -> None:
    try:
        data = json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8")
        _atomic_write(Path(path), data)
    except OSError as exc:
        raise OutputWriteError("写入报告失败", detail=str(exc)) from exc
