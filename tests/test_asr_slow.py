import shutil
import subprocess
from pathlib import Path

import pytest

from subalign.asr import WhisperCppBackend, resolve_model
from subalign.errors import AsrFailed


@pytest.mark.slow
def test_real_whisper_cpp_transcribes_synthetic_speech(tmp_path: Path):
    if not shutil.which("say"):
        pytest.skip("macOS say is unavailable")
    try:
        model = resolve_model("large-v3-turbo")
    except AsrFailed:
        pytest.skip("no GGML model in ~/.cache/whisper")
    wav = tmp_path / "speech.wav"
    try:
        subprocess.run(
            ["say", "-v", "Tingting", "-o", str(wav),
             "--data-format=LEI16@16000", "这是一个字幕时间轴对齐测试。"],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        pytest.skip("Tingting voice is unavailable")
    result = WhisperCppBackend().transcribe(str(wav), lang="zh", model=str(model))
    assert result.tokens
    assert any(token.end > token.start for token in result.tokens)
    assert result.language in ("zh", "chinese", "Chinese")
