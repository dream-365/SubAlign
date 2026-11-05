"""End-to-end orchestration with stage timing and stop-before-write errors."""

from __future__ import annotations

import json
import tempfile
import time
import uuid
from pathlib import Path

from . import __version__
from .align import align
from .asr import WhisperCppBackend
from .errors import AmbiguousFit, LowCoverage
from .fit import apply_model, select_model
from .io import write_report, write_subtitle
from .media import extract_audio
from .report import build_report, validate_report
from .subtitle import group_bilingual, parse_subtitle

COVERAGE_THRESHOLD = 0.30


def run(video: str, subtitle: str, out: str, *, lang: str = "auto",
        model: str = "large-v3-turbo", max_offset: float = 60.0,
        shift: float = 0.0,
        dry_run: bool = False, force: bool = False, keep_temp: bool = False,
        report_path: str | None = None, asr_backend=None,
        ffmpeg: str | None = None, ffprobe: str | None = None) -> dict:
    stage_timings: dict[str, float] = {
        "media": 0.0, "asr": 0.0, "align": 0.0, "fit": 0.0, "write": 0.0,
    }
    warnings: list[str] = []
    run_id = uuid.uuid4().hex
    report_path = report_path or f"{out}.report.json"
    backend = asr_backend or WhisperCppBackend()
    temp_dir = tempfile.mkdtemp(prefix="subalign-")
    wav_path = str(Path(temp_dir) / "audio.wav")

    try:
        doc = parse_subtitle(subtitle)
        started = time.perf_counter()
        audio_info = extract_audio(video, wav_path, ffmpeg=ffmpeg, ffprobe=ffprobe)
        stage_timings["media"] = time.perf_counter() - started

        started = time.perf_counter()
        asr_result = backend.transcribe(wav_path, lang=lang, model=model)
        stage_timings["asr"] = time.perf_counter() - started
        warnings.extend(asr_result.warnings)
        target_lang = asr_result.language if lang == "auto" else lang
        tool_versions = {
            "subalign": __version__,
            "whisper_cpp": asr_result.version,
            "model_file": asr_result.model_path,
            "model_sha256": asr_result.model_sha256,
            "ffmpeg": audio_info.ffmpeg_version,
        }

        started = time.perf_counter()
        groups = group_bilingual(doc, target_lang)
        anchors = align(doc, groups, asr_result.tokens, max_offset=max_offset)
        stage_timings["align"] = time.perf_counter() - started
        try:
            anchor_dump = []
            for anchor in anchors:
                cue = doc.cue(anchor.cue_index)
                anchor_dump.append({
                    "cue_index": anchor.cue_index,
                    "start": round(cue.start, 3) if cue else None,
                    "audio_start": round(anchor.audio_start, 3),
                    "audio_end": round(anchor.audio_end, 3),
                    "matched_ratio": round(anchor.matched_ratio, 4),
                    "confidence": anchor.confidence,
                    "group_id": anchor.group_id,
                })
            Path(f"{report_path}.anchors.json").write_text(
                json.dumps(anchor_dump, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except OSError:
            pass

        started = time.perf_counter()
        offset_model, ambiguous, fit_warnings = select_model(anchors, doc.cues)
        warnings.extend(fit_warnings)
        if shift:
            if offset_model.kind == "piecewise":
                offset_model.segment_offsets = [
                    value + shift for value in offset_model.segment_offsets
                ]
            else:
                offset_model.intercept += shift
        if offset_model.rmse > 0.10:
            warnings.append(f"WARN_RMSE: {offset_model.rmse:.3f}s")
        adjustments, coverage, clamp_warnings = apply_model(doc, offset_model, anchors, groups)
        warnings.extend(clamp_warnings)
        stage_timings["fit"] = time.perf_counter() - started

        if coverage < COVERAGE_THRESHOLD:
            report = build_report(run_id, doc, offset_model, adjustments, warnings,
                                  stage_timings, coverage, tool_versions)
            validate_report(report)
            write_report(report, report_path)
            raise LowCoverage(
                f"锚点覆盖率 {coverage:.1%} 低于 {COVERAGE_THRESHOLD:.0%}",
                detail=f"报告已写入 {report_path}",
            )
        if ambiguous and not force:
            report = build_report(run_id, doc, offset_model, adjustments, warnings,
                                  stage_timings, coverage, tool_versions)
            validate_report(report)
            write_report(report, report_path)
            raise AmbiguousFit(
                "分段模型断点不稳定，默认不写回",
                detail=f"报告已写入 {report_path}；确认后可加 --force",
            )

        started = time.perf_counter()
        if not dry_run:
            write_subtitle(doc, adjustments, out, force=force)
        stage_timings["write"] = time.perf_counter() - started

        report = build_report(run_id, doc, offset_model, adjustments, warnings,
                              stage_timings, coverage, tool_versions)
        validate_report(report)
        write_report(report, report_path)
        if keep_temp:
            report["warnings"].append(f"WARN_KEEP_TEMP: {wav_path}")
            write_report(report, report_path)
        return report
    finally:
        if not keep_temp:
            for path in Path(temp_dir).glob("*"):
                try:
                    path.unlink()
                except OSError:
                    pass
            try:
                Path(temp_dir).rmdir()
            except OSError:
                pass
