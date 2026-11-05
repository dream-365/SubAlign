"""Audio extraction and the fixed PCM s16le input contract."""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from ..errors import MediaDecodeError, MediaFormatError, NoAudio
from ..subtitle.model import AudioInfo

Runner = Callable[..., subprocess.CompletedProcess]

TARGET_SAMPLE_RATE = 16000
TARGET_CHANNELS = 1
TARGET_CODEC = "pcm_s16le"


def _default_runner(cmd: Sequence[str], **kwargs) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    libdir = Path(os.environ.get("SUBALIGN_LIBDIR", str(Path.home() / ".local" / "lib")))
    if libdir.is_dir() and any(libdir.glob("libwhisper*.dylib")):
        existing = env.get("DYLD_LIBRARY_PATH", "")
        env["DYLD_LIBRARY_PATH"] = str(libdir) + (f":{existing}" if existing else "")
    return subprocess.run(cmd, capture_output=True, text=True, env=env, **kwargs)


def _candidates(name: str, env_var: str) -> list[str]:
    values: list[str] = []
    override = os.environ.get(env_var)
    if override:
        values.append(override)
    found = shutil.which(name)
    if found:
        values.append(found)
    patterns = [
        f"/opt/homebrew/Cellar/ffmpeg*/**/bin/{name}",
        f"/usr/local/Cellar/ffmpeg*/**/bin/{name}",
        f"/opt/homebrew/bin/{name}",
        f"/usr/local/bin/{name}",
    ]
    for pattern in patterns:
        values.extend(glob.glob(pattern, recursive=True))
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        if value not in seen and Path(value).exists():
            seen.add(value)
            unique.append(value)
    return unique


def find_binary(name: str, env_var: str, runner: Runner | None = None) -> str:
    runner = runner or _default_runner
    errors: list[str] = []
    for candidate in _candidates(name, env_var):
        try:
            result = runner([candidate, "-version"])
        except OSError as exc:
            errors.append(f"{candidate}: {exc}")
            continue
        if result.returncode == 0:
            return candidate
        tail = (result.stderr or result.stdout or "").strip().splitlines()
        errors.append(f"{candidate}: {tail[0] if tail else 'exit ' + str(result.returncode)}")
    hint = "；".join(errors[-2:]) if errors else "PATH 中未找到"
    raise MediaDecodeError(
        f"{name} 不可用",
        detail=f"{hint}。可用 FFMPEG_BIN/FFPROBE_BIN 指定可执行文件；"
        "Homebrew 用户可尝试 brew install whisper.cpp rubberband 或 brew reinstall ffmpeg",
    )


def probe_audio(video: str | Path, ffprobe: str, runner: Runner | None = None) -> dict:
    runner = runner or _default_runner
    cmd = [
        ffprobe, "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,sample_rate,channels:format=duration",
        "-of", "json", str(video),
    ]
    result = runner(cmd)
    if result.returncode != 0:
        raise MediaDecodeError("ffprobe 无法读取视频", detail=(result.stderr or "").strip()[:400])
    try:
        payload = json.loads(result.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise MediaDecodeError("ffprobe 输出不是 JSON", detail=str(exc)) from exc
    streams = payload.get("streams") or []
    if not streams:
        raise NoAudio("视频没有音轨", detail=str(video))
    stream = streams[0]
    try:
        duration = float(payload.get("format", {}).get("duration") or 0.0)
    except (TypeError, ValueError):
        duration = 0.0
    return {
        "codec": stream.get("codec_name", ""),
        "sample_rate": int(stream.get("sample_rate") or 0),
        "channels": int(stream.get("channels") or 0),
        "duration": duration,
    }


def verify_wav(wav: str | Path, ffprobe: str, duration: float,
               runner: Runner | None = None, ffmpeg_version: str = "") -> AudioInfo:
    info = probe_audio(wav, ffprobe, runner)
    problems = []
    if info["codec"] != TARGET_CODEC:
        problems.append(f"codec={info['codec'] or 'unknown'}")
    if info["sample_rate"] != TARGET_SAMPLE_RATE:
        problems.append(f"sample_rate={info['sample_rate']}")
    if info["channels"] != TARGET_CHANNELS:
        problems.append(f"channels={info['channels']}")
    if problems:
        raise MediaFormatError(
            "抽取的音频不符合 16kHz / 单声道 / PCM s16le 契约",
            detail=", ".join(problems),
        )
    return AudioInfo(
        path=str(wav),
        duration=info["duration"] or duration,
        sample_rate=info["sample_rate"],
        channels=info["channels"],
        codec=info["codec"],
        ffmpeg_version=ffmpeg_version,
    )


def extract_audio(video: str | Path, out_wav: str | Path,
                  ffmpeg: str | None = None, ffprobe: str | None = None,
                  runner: Runner | None = None) -> AudioInfo:
    runner = runner or _default_runner
    ffmpeg = ffmpeg or find_binary("ffmpeg", "FFMPEG_BIN", runner)
    ffprobe = ffprobe or find_binary("ffprobe", "FFPROBE_BIN", runner)
    version_result = runner([ffmpeg, "-version"])
    ffmpeg_version = (
        (version_result.stdout or "").splitlines()[0]
        if version_result.returncode == 0 and version_result.stdout else ""
    )
    source = probe_audio(video, ffprobe, runner)
    cmd = [
        ffmpeg, "-y", "-v", "error", "-i", str(video),
        "-vn", "-sn", "-dn",
        "-ar", str(TARGET_SAMPLE_RATE), "-ac", str(TARGET_CHANNELS),
        "-c:a", TARGET_CODEC, str(out_wav),
    ]
    result = runner(cmd)
    if result.returncode != 0:
        raise MediaDecodeError(
            "ffmpeg 音轨抽取失败",
            detail=(result.stderr or "").strip()[:400],
        )
    return verify_wav(out_wav, ffprobe, source["duration"], runner, ffmpeg_version)
