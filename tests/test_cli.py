from pathlib import Path

from subalign.cli import main


def _inputs(tmp_path: Path):
    video = tmp_path / "video.mp4"
    video.write_bytes(b"")
    subtitle = tmp_path / "sub.srt"
    subtitle.write_text("1\n00:00:01,000 --> 00:00:02,000\nhello\n", encoding="utf-8")
    return video, subtitle


def test_contract_ok(monkeypatch, tmp_path):
    video, subtitle = _inputs(tmp_path)
    out = tmp_path / "out.srt"
    called = {}

    def fake_run(*args, **kwargs):
        called.update(kwargs)
        return {"model": {"kind": "constant"}, "coverage": 1.0}

    monkeypatch.setattr("subalign.cli.run", fake_run)
    assert main(["align", "--video", str(video), "--subtitle", str(subtitle), "--out", str(out)]) == 0
    assert called["dry_run"] is False


def test_dry_run_flag_passthrough(monkeypatch, tmp_path):
    video, subtitle = _inputs(tmp_path)
    out = tmp_path / "out.srt"
    called = {}

    def fake_run(*args, **kwargs):
        called.update(kwargs)
        return {"model": {"kind": "constant"}, "coverage": 1.0}

    monkeypatch.setattr("subalign.cli.run", fake_run)
    assert main(["align", "--video", str(video), "--subtitle", str(subtitle),
                 "--out", str(out), "--dry-run"]) == 0
    assert called["dry_run"] is True


def test_missing_video_exit_1(tmp_path):
    _, subtitle = _inputs(tmp_path)
    code = main(["align", "--video", str(tmp_path / "nope.mp4"),
                 "--subtitle", str(subtitle), "--out", str(tmp_path / "out.srt")])
    assert code == 1


def test_out_same_as_input_exit_1(tmp_path):
    video, subtitle = _inputs(tmp_path)
    code = main(["align", "--video", str(video), "--subtitle", str(subtitle),
                 "--out", str(subtitle)])
    assert code == 1


def test_extension_mismatch_exit_1(tmp_path):
    video, subtitle = _inputs(tmp_path)
    code = main(["align", "--video", str(video), "--subtitle", str(subtitle),
                 "--out", str(tmp_path / "out.ass")])
    assert code == 1


def test_output_exists_exit_5(tmp_path):
    video, subtitle = _inputs(tmp_path)
    out = tmp_path / "out.srt"
    out.write_text("exists", encoding="utf-8")
    code = main(["align", "--video", str(video), "--subtitle", str(subtitle),
                 "--out", str(out)])
    assert code == 5


def test_bad_max_offset_exit_1(tmp_path):
    video, subtitle = _inputs(tmp_path)
    code = main(["align", "--video", str(video), "--subtitle", str(subtitle),
                 "--out", str(tmp_path / "out.srt"), "--max-offset", "0"])
    assert code == 1
