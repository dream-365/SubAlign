import json
from pathlib import Path

import pytest

from subalign.errors import LowCoverage
from subalign.pipeline import run
from subalign.subtitle.model import AsrResult, AsrToken, AudioInfo


class FakeBackend:
    def __init__(self, tokens):
        self.tokens = tokens

    def transcribe(self, wav, lang="auto", model="large-v3-turbo"):
        return AsrResult(self.tokens, "zh", True, [])


def _patch_media(monkeypatch):
    monkeypatch.setattr(
        "subalign.pipeline.extract_audio",
        lambda *args, **kwargs: AudioInfo("audio.wav", 10.0, 16000, 1, "pcm_s16le"),
    )


def _subtitle(tmp_path: Path) -> Path:
    path = tmp_path / "sub.srt"
    path.write_text(
        "1\n00:00:01,000 --> 00:00:02,000\n你好世界\n\n"
        "2\n00:00:04,000 --> 00:00:05,000\n第二句\n",
        encoding="utf-8",
    )
    return path


def test_end_to_end_with_fake_asr(monkeypatch, tmp_path):
    _patch_media(monkeypatch)
    subtitle = _subtitle(tmp_path)
    before = subtitle.read_bytes()
    out = tmp_path / "out.srt"
    report_path = tmp_path / "report.json"
    tokens = [
        AsrToken("你好", 0.0, 0.5, 0.9),
        AsrToken("世界", 0.5, 1.0, 0.9),
        AsrToken("第二句", 2.5, 3.5, 0.9),
    ]
    report = run("video.mp4", str(subtitle), str(out), asr_backend=FakeBackend(tokens),
                 force=True, report_path=str(report_path))
    assert out.exists()
    assert subtitle.read_bytes() == before
    assert report["format"] == "srt"
    assert report["coverage"] == 1.0
    assert report_path.exists()
    assert json.loads(report_path.read_text(encoding="utf-8"))["run_id"] == report["run_id"]


def test_shift_applies_after_model(monkeypatch, tmp_path):
    _patch_media(monkeypatch)
    subtitle = _subtitle(tmp_path)
    tokens = [
        AsrToken("你好", 0.0, 0.5, 0.9),
        AsrToken("世界", 0.5, 1.0, 0.9),
        AsrToken("第二句", 2.5, 3.5, 0.9),
    ]
    out_a = tmp_path / "a.srt"
    out_b = tmp_path / "b.srt"
    run("video.mp4", str(subtitle), str(out_a), asr_backend=FakeBackend(tokens),
        force=True, report_path=str(tmp_path / "a.json"))
    run("video.mp4", str(subtitle), str(out_b), asr_backend=FakeBackend(tokens),
        shift=0.6, force=True, report_path=str(tmp_path / "b.json"))
    from subalign.subtitle import parse_subtitle
    a = parse_subtitle(out_a).cues[1].start
    b = parse_subtitle(out_b).cues[1].start
    assert abs((b - a) - 0.6) < 1e-6


def test_dry_run_does_not_write_subtitle(monkeypatch, tmp_path):
    _patch_media(monkeypatch)
    subtitle = _subtitle(tmp_path)
    out = tmp_path / "out.srt"
    tokens = [AsrToken("你好", 0.0, 0.5, 0.9), AsrToken("世界", 0.5, 1.0, 0.9),
              AsrToken("第二句", 2.5, 3.5, 0.9)]
    run("video.mp4", str(subtitle), str(out), asr_backend=FakeBackend(tokens),
        dry_run=True, force=True, report_path=str(tmp_path / "report.json"))
    assert not out.exists()
    assert (tmp_path / "report.json").exists()


def test_low_coverage_stops_before_write(monkeypatch, tmp_path):
    _patch_media(monkeypatch)
    subtitle = _subtitle(tmp_path)
    out = tmp_path / "out.srt"
    tokens = [AsrToken("完全无关", 90.0, 91.0, 0.9)]
    with pytest.raises(LowCoverage):
        run("video.mp4", str(subtitle), str(out), asr_backend=FakeBackend(tokens),
            force=True, report_path=str(tmp_path / "report.json"))
    assert not out.exists()
    assert (tmp_path / "report.json").exists()
