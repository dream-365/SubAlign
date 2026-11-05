"""Typed errors with the exit codes defined in the Spec."""

from __future__ import annotations


class SubAlignError(Exception):
    code = "ERR_INTERNAL"
    exit_code = 6

    def __init__(self, message: str, *, detail: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail

    def __str__(self) -> str:
        if self.detail:
            return f"{self.code}: {self.message} ({self.detail})"
        return f"{self.code}: {self.message}"


class InputInvalid(SubAlignError):
    code = "ERR_INPUT_INVALID"
    exit_code = 1


class OutputExists(SubAlignError):
    code = "ERR_OUTPUT_EXISTS"
    exit_code = 5


class SubtitleParseError(SubAlignError):
    code = "ERR_SUBTITLE_PARSE"
    exit_code = 1


class NoAudio(SubAlignError):
    code = "ERR_NO_AUDIO"
    exit_code = 2


class MediaDecodeError(SubAlignError):
    code = "ERR_MEDIA_DECODE"
    exit_code = 2


class MediaFormatError(SubAlignError):
    code = "ERR_MEDIA_FORMAT"
    exit_code = 2


class AsrFailed(SubAlignError):
    code = "ERR_ASR_FAILED"
    exit_code = 2


class LowCoverage(SubAlignError):
    code = "ERR_LOW_COVERAGE"
    exit_code = 3


class AmbiguousFit(SubAlignError):
    code = "ERR_AMBIGUOUS_FIT"
    exit_code = 4


class OutputWriteError(SubAlignError):
    code = "ERR_OUTPUT_WRITE"
    exit_code = 2
