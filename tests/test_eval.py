from pathlib import Path

from eval.precision import compare_documents, percentile
from subalign.subtitle import parse_subtitle


def _ts(seconds: float) -> str:
    total_ms = int(round(seconds * 1000))
    hours, rem = divmod(total_ms, 3_600_000)
    minutes, rem = divmod(rem, 60_000)
    secs, millis = divmod(rem, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _write(path: Path, times):
    body = []
    for index, (start, end, text) in enumerate(times, start=1):
        body.append(f"{index}\n{_ts(start)} --> {_ts(end)}\n{text}\n")
    path.write_text("\n".join(body), encoding="utf-8")


def test_compare_documents_and_percentile(tmp_path: Path):
    truth = tmp_path / "truth.srt"
    pred = tmp_path / "pred.srt"
    _write(truth, [(1, 2, "你好"), (5, 6, "世界")])
    _write(pred, [(1.05, 2.1, "你好"), (5.2, 6.05, "世界")])
    result = compare_documents(parse_subtitle(truth), parse_subtitle(pred))
    assert result["matched"] == 2
    assert result["start"]["median"] == 0.125
    assert result["start"]["max"] == 0.2
    assert result["by_lang"]["zh"]["start"]["count"] == 2
    assert percentile([0.0, 1.0], 0.5) == 0.5
