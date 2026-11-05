"""whisper.cpp adapter: DTW token timestamps with a heuristic fallback."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from pathlib import Path

from ..errors import AsrFailed
from ..subtitle.model import AsrResult, AsrToken

Runner = Callable[..., subprocess.CompletedProcess]

_DTW_NAMES = {
    "large-v3-turbo": "large.v3.turbo",
    "large-v3": "large.v3",
    "large-v2": "large.v2",
    "large-v1": "large.v1",
    "medium": "medium",
    "small": "small",
    "base": "base",
    "tiny": "tiny",
}


def find_whisper_binary() -> str:
    override = os.environ.get("WHISPER_CLI")
    candidates = [override] if override else []
    for name in ("whisper-cli", "whisper", "main", "whisper-cpp"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    raise AsrFailed("找不到 whisper.cpp 可执行文件", detail="可用 WHISPER_CLI 环境变量指定")


def _model_dirs() -> list[Path]:
    dirs = [Path.home() / ".cache" / "whisper", Path.cwd() / "models"]
    override = os.environ.get("WHISPER_MODEL_DIR")
    if override:
        dirs.insert(0, Path(override))
    return dirs


def resolve_model(name: str) -> Path:
    candidate = Path(name).expanduser()
    if candidate.exists():
        return candidate
    logical = name[:-4] if name.endswith(".bin") else name
    for directory in _model_dirs():
        for filename in (f"ggml-{logical}.bin", f"{logical}.bin", f"ggml-{logical}.gguf"):
            path = directory / filename
            if path.exists():
                return path
    available = sorted(
        str(path) for directory in _model_dirs() if directory.exists()
        for path in directory.glob("ggml-*.bin")
    )
    detail = "可用模型: " + ", ".join(available) if available else "未在 ~/.cache/whisper 或 models/ 找到 GGML 模型"
    raise AsrFailed(f"找不到模型 {name}", detail=detail)


def dtw_name(model_path: Path) -> str | None:
    stem = model_path.name.lower().removeprefix("ggml-").removesuffix(".bin").removesuffix(".gguf")
    return _DTW_NAMES.get(stem)


_HASH_CACHE: dict[tuple[str, int, int], str] = {}


def model_sha256(path: Path) -> str:
    stat = path.stat()
    key = (str(path), stat.st_size, int(stat.st_mtime))
    if key not in _HASH_CACHE:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        _HASH_CACHE[key] = digest.hexdigest()
    return _HASH_CACHE[key]


def whisper_version(binary: str, runner: Runner) -> str:
    try:
        result = runner([binary, "--version"])
    except OSError:
        return ""
    text = ((result.stdout or "") + (result.stderr or "")).strip()
    return text.splitlines()[0] if result.returncode == 0 and text else ""


def _tokens_from_payload(payload: dict) -> tuple[list[AsrToken], bool]:
    tokens: list[AsrToken] = []
    dtw_used = False
    segments = payload.get("transcription") or []
    if not segments and payload.get("text"):
        return [AsrToken(text=payload["text"], start=0.0, end=0.0, score=0.0)], False
    for segment in segments:
        for token in segment.get("tokens") or []:
            text = (token.get("text") or "").strip()
            if not text or (text.startswith("[") and text.endswith("]")):
                continue
            offsets = token.get("offsets") or {}
            start = float(offsets.get("from", 0)) / 1000.0
            end = float(offsets.get("to", 0)) / 1000.0
            if end < start:
                continue
            if end == start:
                end = start + 0.01
            tokens.append(
                AsrToken(
                    text=text,
                    start=start,
                    end=end,
                    score=float(token.get("p", 0.0) or 0.0),
                )
            )
            if int(token.get("t_dtw", -1)) >= 0:
                dtw_used = True
    if not tokens:
        for segment in segments:
            text = (segment.get("text") or "").strip()
            offsets = segment.get("offsets") or {}
            start = float(offsets.get("from", 0)) / 1000.0
            end = float(offsets.get("to", 0)) / 1000.0
            if text and end > start:
                tokens.append(AsrToken(text=text, start=start, end=end, score=0.0))
    tokens.sort(key=lambda token: (token.start, token.end))
    return tokens, dtw_used


class WhisperCppBackend:
    def __init__(self, binary: str | None = None, runner: Runner | None = None,
                 threads: int | None = None) -> None:
        self.binary = binary
        self.runner = runner or (lambda cmd, **kwargs: subprocess.run(cmd, capture_output=True, text=True, **kwargs))
        self.threads = threads

    def _command(self, wav: str, lang: str, model_path: Path, out_base: str,
                 dtw: str | None, no_flash_attn: bool) -> list[str]:
        assert self.binary
        cmd = [
            self.binary, "-m", str(model_path), "-f", wav,
            "-l", lang, "-ojf", "-of", out_base, "-np",
        ]
        if self.threads:
            cmd.extend(["-t", str(self.threads)])
        if dtw:
            cmd.append("--dtw")
            cmd.append(dtw)
            if no_flash_attn:
                cmd.append("-nfa")
        return cmd

    def transcribe(self, wav: str, lang: str = "auto", model: str = "large-v3-turbo") -> AsrResult:
        self.binary = self.binary or find_whisper_binary()
        model_path = resolve_model(model)
        model_hash = model_sha256(model_path)
        version = whisper_version(self.binary, self.runner)
        out_base = str(Path(wav).with_suffix(".whisper"))
        json_path = Path(out_base + ".json")
        warnings: list[str] = []
        dtw = dtw_name(model_path)

        attempts: list[tuple[str | None, bool]] = []
        if dtw:
            attempts.append((dtw, True))
        attempts.append((None, False))

        stderr_tail = ""
        for dtw_value, no_flash_attn in attempts:
            if json_path.exists():
                json_path.unlink()
            cmd = self._command(wav, lang, model_path, out_base, dtw_value, no_flash_attn)
            result = self.runner(cmd)
            stderr_tail = (result.stderr or "").strip()[-400:]
            if result.returncode == 0 and json_path.exists():
                try:
                    payload = json.loads(json_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    raise AsrFailed("whisper.cpp 输出 JSON 无法解析", detail=str(exc)) from exc
                finally:
                    if json_path.exists():
                        json_path.unlink()
                tokens, t_dtw_seen = _tokens_from_payload(payload)
                if not tokens:
                    raise AsrFailed("whisper.cpp 没有返回 token", detail=stderr_tail)
                used_dtw = bool(dtw_value and t_dtw_seen)
                if dtw_value and not t_dtw_seen:
                    warnings.append("WARN_NO_DTW")
                detected = (payload.get("result") or {}).get("language") or (payload.get("params") or {}).get("language") or lang
                return AsrResult(
                    tokens=tokens,
                    language=detected,
                    dtw_used=used_dtw,
                    warnings=warnings,
                    binary=self.binary,
                    version=version,
                    model_path=str(model_path),
                    model_sha256=model_hash,
                )
            if dtw_value:
                warnings.append("WARN_NO_DTW")

        raise AsrFailed("whisper.cpp 识别失败", detail=stderr_tail or "未生成 JSON")
