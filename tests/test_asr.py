import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from subalign.asr.whisper_cpp import WhisperCppBackend
from subalign.errors import AsrFailed


def _result(returncode=0, stderr=""):
    return SimpleNamespace(returncode=returncode, stdout="", stderr=stderr)


def _payload(t_dtw=10):
    return {
        "result": {"language": "zh"},
        "params": {"language": "zh"},
        "transcription": [{
            "text": "你好世界",
            "tokens": [
                {"text": "[_BEG_]", "offsets": {"from": 0, "to": 0}, "p": 1.0, "t_dtw": -1},
                {"text": "你好", "offsets": {"from": 0, "to": 500}, "p": 0.9, "t_dtw": t_dtw},
                {"text": "世界", "offsets": {"from": 500, "to": 1000}, "p": 0.8, "t_dtw": t_dtw},
            ],
        }],
    }


def _writer(payload, calls=None):
    def runner(cmd):
        if calls is not None:
            calls.append(cmd)
        if "--version" in cmd:
            return SimpleNamespace(returncode=0, stdout="whisper.cpp version: test\n", stderr="")
        out_base = Path(cmd[cmd.index("-of") + 1])
        (out_base.parent / (out_base.name + ".json")).write_text(
            json.dumps(payload), encoding="utf-8"
        )
        return _result(stderr="dtw = 1")
    return runner


def _model(tmp_path: Path) -> Path:
    path = tmp_path / "ggml-large-v3-turbo.bin"
    path.write_bytes(b"")
    return path


def test_parses_tokens_and_dtw(tmp_path):
    backend = WhisperCppBackend(binary="/fake/whisper", runner=_writer(_payload()))
    result = backend.transcribe(str(tmp_path / "audio.wav"), model=str(_model(tmp_path)))
    assert result.language == "zh"
    assert result.dtw_used is True
    assert [token.text for token in result.tokens] == ["你好", "世界"]
    assert result.tokens[0].start == 0.0
    assert result.tokens[1].end == 1.0


def test_falls_back_without_dtw(tmp_path):
    calls = []

    def runner(cmd):
        calls.append(cmd)
        if "--version" in cmd:
            return SimpleNamespace(returncode=0, stdout="whisper.cpp version: test\n", stderr="")
        if len([call for call in calls if "--version" not in call]) == 1:
            return _result(returncode=1, stderr="dtw failed")
        out_base = Path(cmd[cmd.index("-of") + 1])
        (out_base.parent / (out_base.name + ".json")).write_text(
            json.dumps(_payload(t_dtw=-1)), encoding="utf-8"
        )
        return _result()

    backend = WhisperCppBackend(binary="/fake/whisper", runner=runner)
    result = backend.transcribe(str(tmp_path / "audio.wav"), model=str(_model(tmp_path)))
    assert len([call for call in calls if "--version" not in call]) == 2
    assert "WARN_NO_DTW" in result.warnings
    assert result.dtw_used is False


def test_zero_duration_tokens_are_kept(tmp_path):
    payload = {
        "result": {"language": "en"},
        "transcription": [{
            "text": "These extreme",
            "tokens": [
                {"text": " These", "offsets": {"from": 21000, "to": 21000}, "p": 0.9, "t_dtw": 1},
                {"text": " extreme", "offsets": {"from": 21000, "to": 21500}, "p": 0.9, "t_dtw": 1},
            ],
        }],
    }
    backend = WhisperCppBackend(binary="/fake/whisper", runner=_writer(payload))
    result = backend.transcribe(str(tmp_path / "audio.wav"), model=str(_model(tmp_path)))
    assert [token.text for token in result.tokens] == ["These", "extreme"]
    assert result.tokens[0].end > result.tokens[0].start


def test_no_tokens_raises(tmp_path):
    payload = {"result": {"language": "zh"}, "transcription": [{"tokens": []}]}
    backend = WhisperCppBackend(binary="/fake/whisper", runner=_writer(payload))
    with pytest.raises(AsrFailed):
        backend.transcribe(str(tmp_path / "audio.wav"), model=str(_model(tmp_path)))
