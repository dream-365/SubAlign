"""Data contracts shared by the subtitle, alignment, fit and output layers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class SubtitleCue:
    index: int
    start: float
    end: float
    text: str
    normalized: str = ""
    lang: str = "mixed"
    group_id: int = 0
    anchor_text: str = ""
    line_pos: int = -1
    settings: str = ""


@dataclass
class SubtitleDocument:
    format: str
    cues: list[SubtitleCue]
    raw_lines: list[str]
    encoding: str = "utf-8"
    bom: bool = False
    ass_format: list[str] = field(default_factory=list)

    @property
    def line_ending(self) -> str:
        for line in self.raw_lines:
            if line.endswith("\r\n"):
                return "\r\n"
            if line.endswith("\n"):
                return "\n"
            if line.endswith("\r"):
                return "\r"
        return "\n"

    def cue(self, index: int) -> SubtitleCue | None:
        for cue in self.cues:
            if cue.index == index:
                return cue
        return None


@dataclass
class BilingualGroup:
    group_id: int
    cue_indices: list[int]
    anchor_cue_index: int
    anchor_lang: str


@dataclass
class Anchor:
    cue_index: int
    group_id: int
    audio_start: float
    audio_end: float
    matched_ratio: float
    confidence: str


@dataclass
class OffsetModel:
    kind: str
    intercept: float = 0.0
    slope: float = 0.0
    breakpoints: list[float] = field(default_factory=list)
    rmse: float = 0.0
    segment_offsets: list[float] = field(default_factory=list)

    def predict(self, t: float) -> float:
        """Return the correction (seconds) that should be added at time t."""
        if self.kind == "constant":
            return self.intercept
        if self.kind == "linear":
            return self.intercept + self.slope * t
        for i, bp in enumerate(self.breakpoints):
            if t < bp:
                return self.segment_offsets[i]
        return self.segment_offsets[-1] if self.segment_offsets else self.intercept


@dataclass
class CueAdjustment:
    cue_index: int
    delta_start: float
    delta_end: float
    final_start: float
    final_end: float
    confidence: str
    segment_id: int
    group_id: int = 0
    anchor_lang: str = "none"


@dataclass
class AudioInfo:
    path: str
    duration: float
    sample_rate: int
    channels: int
    codec: str
    ffmpeg_version: str = ""


@dataclass
class AsrToken:
    text: str
    start: float
    end: float
    score: float = 0.0


@dataclass
class AsrResult:
    tokens: list[AsrToken]
    language: str = "unknown"
    dtw_used: bool = False
    warnings: list[str] = field(default_factory=list)
    binary: str = ""
    version: str = ""
    model_path: str = ""
    model_sha256: str = ""
