"""Alignment report construction and schema validation."""

from __future__ import annotations

import json
from pathlib import Path

from ..subtitle.model import CueAdjustment, OffsetModel, SubtitleDocument

_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs" / "specs" / "SPEC-001-subtitle-timeline-alignment"
    / "schemas" / "report.schema.json"
)


def build_report(run_id: str, doc: SubtitleDocument, model: OffsetModel,
                 adjustments: list[CueAdjustment], warnings: list[str],
                 stage_timings: dict[str, float], coverage: float,
                 tool_versions: dict[str, str] | None = None) -> dict:
    return {
        "run_id": run_id,
        "format": doc.format,
        "tool_versions": tool_versions or {
            "subalign": "", "whisper_cpp": "", "model_file": "",
            "model_sha256": "", "ffmpeg": "",
        },
        "coverage": round(coverage, 6),
        "model": {
            "kind": model.kind,
            "intercept": round(model.intercept, 6),
            "slope": round(model.slope, 9),
            "breakpoints": [round(value, 6) for value in model.breakpoints],
            "rmse": round(model.rmse, 6),
        },
        "adjustments": [
            {
                "cue_index": item.cue_index,
                "delta_start": round(item.delta_start, 6),
                "delta_end": round(item.delta_end, 6),
                "final_start": round(item.final_start, 6),
                "final_end": round(item.final_end, 6),
                "confidence": item.confidence,
                "segment_id": item.segment_id,
                "group_id": item.group_id,
                "anchor_lang": item.anchor_lang,
            }
            for item in adjustments
        ],
        "warnings": warnings,
        "stage_timings": {key: round(value, 3) for key, value in stage_timings.items()},
    }


def validate_report(report: dict) -> None:
    if not _SCHEMA_PATH.exists():
        return
    try:
        import jsonschema
    except ImportError:
        return
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(report, schema)
