from pathlib import Path

import pytest

from subalign.errors import SubtitleParseError
from subalign.io.writer import write_subtitle
from subalign.subtitle import format_ass_time, format_srt_time, parse_subtitle
from subalign.subtitle.model import CueAdjustment
from subalign.subtitle.normalize import detect_lang, normalize_text


def test_srt_parse_and_text(tmp_path: Path):
    path = tmp_path / "a.srt"
    path.write_text(
        "1\n00:00:01,000 --> 00:00:03,000\n你好 world\n\n"
        "2\n00:00:05,500 --> 00:00:07,250\n第二行\n",
        encoding="utf-8",
    )
    doc = parse_subtitle(path)
    assert doc.format == "srt"
    assert len(doc.cues) == 2
    assert doc.cues[0].text == "你好 world"
    assert doc.cues[0].start == 1.0
    assert doc.cues[1].start == 5.5
    assert doc.cues[1].end == 7.25


def test_srt_roundtrip_preserves_text_and_settings(tmp_path: Path):
    path = tmp_path / "a.srt"
    original = "1\n00:00:01,000 --> 00:00:03,000  X1:10 X2:20\nhello  world\n"
    path.write_text(original, encoding="utf-8")
    doc = parse_subtitle(path)
    out = tmp_path / "b.srt"
    write_subtitle(doc, [CueAdjustment(1, 1.0, 1.0, 2.0, 4.0, "high", 0)], out)
    text = out.read_text(encoding="utf-8")
    assert "00:00:02,000 --> 00:00:04,000  X1:10 X2:20" in text
    assert "hello  world" in text


def test_gb18030_roundtrip(tmp_path: Path):
    path = tmp_path / "gb.srt"
    path.write_bytes("1\n00:00:01,000 --> 00:00:02,000\n中文字幕\n".encode("gb18030"))
    doc = parse_subtitle(path)
    assert doc.encoding == "gb18030"
    out = tmp_path / "gb.out.srt"
    write_subtitle(doc, [CueAdjustment(1, 0, 0, 1.0, 2.0, "high", 0)], out)
    assert out.read_bytes().decode("gb18030").startswith("1\n00:00:01,000")


def test_utf8_bom_detected(tmp_path: Path):
    path = tmp_path / "bom.srt"
    path.write_bytes(b"\xef\xbb\xbf" + "1\n00:00:01,000 --> 00:00:02,000\nhello\n".encode())
    doc = parse_subtitle(path)
    assert doc.bom is True
    assert doc.encoding == "utf-8"


def test_ass_preserves_non_time_fields(tmp_path: Path):
    path = tmp_path / "a.ass"
    source = (
        "[Script Info]\nTitle: Test\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname\nStyle: Default,Arial\n\n"
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\\pos(1,2)}你好\n"
        "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Hello\n"
        "Comment: 0,0:00:04.00,0:00:05.00,Default,,0,0,0,,keep me\n"
    )
    path.write_text(source, encoding="utf-8")
    doc = parse_subtitle(path)
    assert doc.format == "ass"
    assert len(doc.cues) == 2
    assert doc.cues[0].text == "{\\pos(1,2)}你好"
    out = tmp_path / "b.ass"
    write_subtitle(doc, [
        CueAdjustment(1, 0, 0, 2.0, 4.0, "high", 0),
        CueAdjustment(2, 0, 0, 2.0, 4.0, "high", 0),
    ], out)
    text = out.read_text(encoding="utf-8")
    assert "Dialogue: 0,0:00:02.00,0:00:04.00,Default,,0,0,0,,{\\pos(1,2)}你好" in text
    assert "Comment: 0,0:00:04.00,0:00:05.00,Default,,0,0,0,,keep me" in text
    assert "Style: Default,Arial" in text


def test_language_detection_ignores_ass_tags(tmp_path: Path):
    path = tmp_path / "tags.ass"
    path.write_text(
        "[Events]\n"
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        "Dialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,"
        "{\\pos(1,2)\\fnArial\\b1}你好世界\n",
        encoding="utf-8",
    )
    doc = parse_subtitle(path)
    assert doc.cues[0].lang == "zh"
    assert doc.cues[0].normalized == "你好世界"


def test_bad_srt_raises(tmp_path: Path):
    path = tmp_path / "bad.srt"
    path.write_text("not a subtitle\n", encoding="utf-8")
    with pytest.raises(SubtitleParseError):
        parse_subtitle(path)


def test_unsupported_extension(tmp_path: Path):
    path = tmp_path / "a.vtt"
    path.write_text("WEBVTT\n", encoding="utf-8")
    with pytest.raises(SubtitleParseError):
        parse_subtitle(path)


def test_time_formatters():
    assert format_srt_time(3661.234) == "01:01:01,234"
    assert format_ass_time(3661.234) == "1:01:01.23"


def test_language_and_normalization():
    assert detect_lang("你好世界") == "zh"
    assert detect_lang("Hello world") == "en"
    assert detect_lang("你好 world") == "en"
    assert normalize_text("Hello, 世界！") == "hello世界"
    assert normalize_text("{\\pos(1,2)}你好", "ass") == "你好"
