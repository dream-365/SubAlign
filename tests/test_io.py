from pathlib import Path

import pytest

from subalign.errors import OutputExists
from subalign.io.writer import write_subtitle
from subalign.report import build_report, validate_report
from subalign.subtitle import parse_subtitle
from subalign.subtitle.model import CueAdjustment, OffsetModel


def _doc(tmp_path: Path):
    path = tmp_path / "a.srt"
    path.write_text("1\n00:00:01,000 --> 00:00:02,000\nhello\n", encoding="utf-8")
    return parse_subtitle(path)


def test_refuses_overwrite_without_force(tmp_path):
    doc = _doc(tmp_path)
    out = tmp_path / "out.srt"
    out.write_text("exists", encoding="utf-8")
    with pytest.raises(OutputExists):
        write_subtitle(doc, [CueAdjustment(1, 0, 0, 1, 2, "high", 0)], out)
    write_subtitle(doc, [CueAdjustment(1, 0, 0, 1, 2, "high", 0)], out, force=True)
    assert "00:00:01,000 --> 00:00:02,000" in out.read_text(encoding="utf-8")


def test_report_schema_accepts_valid_report(tmp_path):
    doc = _doc(tmp_path)
    model = OffsetModel("constant", intercept=0.0, segment_offsets=[0.0])
    report = build_report("run-1", doc, model,
                          [CueAdjustment(1, 0, 0, 1, 2, "high", 0)],
                          [], {"media": 0.1, "asr": 2.0, "align": 0.2,
                               "fit": 0.1, "write": 0.05}, 1.0)
    validate_report(report)


def test_report_schema_rejects_missing_stage(tmp_path):
    import jsonschema
    doc = _doc(tmp_path)
    model = OffsetModel("constant")
    report = build_report("run-1", doc, model, [], [], {"media": 0.0}, 0.0)
    with pytest.raises(jsonschema.ValidationError):
        validate_report(report)
