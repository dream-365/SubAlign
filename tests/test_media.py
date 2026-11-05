import json
from types import SimpleNamespace

import pytest

from subalign.errors import MediaFormatError, NoAudio
from subalign.media import ffmpeg as media


def _result(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def _probe_payload(codec, rate, channels, duration="10.0"):
    return json.dumps({
        "streams": [{"codec_name": codec, "sample_rate": str(rate), "channels": channels}],
        "format": {"duration": duration},
    })


def test_probe_audio_parses_json():
    def runner(cmd):
        return _result(stdout=_probe_payload("aac", 44100, 2))

    info = media.probe_audio("video.mp4", "/fake/ffprobe", runner)
    assert info["codec"] == "aac"
    assert info["sample_rate"] == 44100
    assert info["channels"] == 2
    assert info["duration"] == 10.0


def test_probe_no_audio():
    def runner(cmd):
        return _result(stdout=json.dumps({"streams": [], "format": {}}))

    with pytest.raises(NoAudio):
        media.probe_audio("video.mp4", "/fake/ffprobe", runner)


def test_extract_audio_builds_fixed_format_command():
    calls = []

    def runner(cmd):
        calls.append(cmd)
        if cmd[0] == "/fake/ffprobe":
            target = cmd[-1]
            if target.endswith(".wav"):
                return _result(stdout=_probe_payload("pcm_s16le", 16000, 1))
            return _result(stdout=_probe_payload("aac", 48000, 2))
        return _result()

    info = media.extract_audio("video.mp4", "audio.wav", ffmpeg="/fake/ffmpeg",
                               ffprobe="/fake/ffprobe", runner=runner)
    assert info.codec == "pcm_s16le"
    ffmpeg_call = [call for call in calls if call[0] == "/fake/ffmpeg" and "-ar" in call][0]
    assert ffmpeg_call[ffmpeg_call.index("-ar") + 1] == "16000"
    assert ffmpeg_call[ffmpeg_call.index("-ac") + 1] == "1"
    assert ffmpeg_call[ffmpeg_call.index("-c:a") + 1] == "pcm_s16le"


def test_verify_wav_rejects_wrong_format():
    def runner(cmd):
        return _result(stdout=_probe_payload("pcm_s16le", 44100, 2))

    with pytest.raises(MediaFormatError):
        media.verify_wav("audio.wav", "/fake/ffprobe", 10.0, runner)


def test_find_binary_skips_broken_candidate(monkeypatch):
    monkeypatch.setattr(media, "_candidates", lambda name, env: ["/bad", "/good"])

    def runner(cmd):
        if cmd[0] == "/bad":
            return _result(returncode=1, stderr="dyld: missing library")
        return _result(returncode=0)

    assert media.find_binary("ffmpeg", "FFMPEG_BIN", runner) == "/good"
