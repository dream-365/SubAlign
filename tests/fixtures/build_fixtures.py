"""Generate the SRT/ASS regression fixtures and eval pairs.

Run from the repository root:
    .venv/bin/python tests/fixtures/build_fixtures.py
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent
CASES = ["global", "linear", "piecewise", "aligned"]

BASE = [
    (1, 0.0, 2.5, "你好世界", "Hello world"),
    (2, 5.0, 7.5, "这是第二句", "This is the second line"),
    (3, 10.0, 12.5, "第三句字幕", "The third subtitle line"),
    (4, 15.0, 17.5, "最后一句", "The last line"),
]


def shift(case: str, t: float) -> float:
    if case == "global":
        return 2.0
    if case == "linear":
        return 0.5 + 0.0004 * t
    if case == "piecewise":
        return 2.0 if t < 10.0 else 4.0
    return 0.0


def _srt_time(seconds: float) -> str:
    total_ms = max(0, int(round(seconds * 1000)))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _ass_time(seconds: float) -> str:
    total_cs = max(0, int(round(seconds * 100)))
    hours, rem = divmod(total_cs, 360_000)
    minutes, rem = divmod(rem, 6_000)
    secs, centis = divmod(rem, 100)
    return f"{hours:d}:{minutes:02d}:{secs:02d}.{centis:02d}"


def _srt(times, bilingual: bool) -> str:
    blocks = []
    for index, start, end, zh, en in times:
        text = f"{zh}\n{en}" if bilingual else zh
        blocks.append(
            f"{index}\n"
            f"{_srt_time(start)} --> {_srt_time(end)}\n"
            f"{text}\n"
        )
    return "\n".join(blocks)


def _ass(times, bilingual: bool) -> str:
    head = [
        "[Script Info]",
        "Title: SubAlign fixture",
        "ScriptType: v4.00+",
        "",
        "[V4+ Styles]",
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial,20,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1",
        "",
        "[Events]",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    lines = []
    for _, start, end, zh, en in times:
        text = f"{zh}\\N{en}" if bilingual else zh
        lines.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(end)},Default,,0,0,0,,{text}"
        )
    return "\r\n".join(head + lines) + "\r\n"


def _times(case: str, offset_noise: float = 0.0):
    result = []
    for index, start, end, zh, en in BASE:
        delta = shift(case, start) + offset_noise
        result.append((index, start + delta, end + delta, zh, en))
    return result


def build() -> None:
    for case in CASES:
        bilingual = case in ("linear", "aligned")
        (ROOT / f"{case}.srt").write_text(_srt(_times(case), bilingual), encoding="utf-8")
        (ROOT / f"{case}.ass").write_text(_ass(_times(case), bilingual), encoding="utf-8", newline="")

    eval_root = ROOT / "eval"
    for case in CASES:
        case_dir = eval_root / case
        case_dir.mkdir(parents=True, exist_ok=True)
        (case_dir / "truth.srt").write_text(_srt(_times("aligned"), False), encoding="utf-8")
        predicted = []
        for index, start, end, zh, en in BASE:
            offset = 0.0 if case == "aligned" else 0.02
            predicted.append((index, start + offset, end - offset, zh, en))
        (case_dir / "pred.srt").write_text(_srt(predicted, False), encoding="utf-8")

    (ROOT / "README.md").write_text(
        "# Fixtures\n\n"
        "- `<case>.srt` / `<case>.ass`: misaligned inputs for global, linear, piecewise and aligned cases.\n"
        "- `eval/<case>/truth.srt` + `pred.srt`: pairs for `eval/precision.py`.\n"
        "- Regenerate with `.venv/bin/python tests/fixtures/build_fixtures.py`.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build()
    print(f"built fixtures in {ROOT}")
