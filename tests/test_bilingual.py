from pathlib import Path

from subalign.subtitle import group_bilingual, parse_subtitle


def _write(tmp_path: Path, body: str):
    path = tmp_path / "bi.srt"
    path.write_text(body, encoding="utf-8")
    return parse_subtitle(path)


def test_groups_overlapping_zh_en(tmp_path):
    doc = _write(tmp_path, (
        "1\n00:00:01,000 --> 00:00:03,000\n你好世界\n\n"
        "2\n00:00:01,000 --> 00:00:03,000\nHello world\n\n"
        "3\n00:00:09,000 --> 00:00:11,000\n再见\n"
    ))
    groups = group_bilingual(doc, "zh")
    assert len(groups) == 1
    assert groups[0].cue_indices == [1, 2]
    assert groups[0].anchor_cue_index == 1
    assert groups[0].anchor_lang == "zh"
    assert doc.cues[0].group_id == 1
    assert doc.cues[1].group_id == 1
    assert doc.cues[2].group_id == 0


def test_no_group_below_overlap_threshold(tmp_path):
    doc = _write(tmp_path, (
        "1\n00:00:01,000 --> 00:00:05,000\n你好世界\n\n"
        "2\n00:00:04,000 --> 00:00:06,000\nHello world\n"
    ))
    assert group_bilingual(doc, "zh") == []


def test_anchor_follows_asr_language(tmp_path):
    doc = _write(tmp_path, (
        "1\n00:00:01,000 --> 00:00:03,000\n你好世界\n\n"
        "2\n00:00:01,000 --> 00:00:03,000\nHello world\n"
    ))
    groups = group_bilingual(doc, "en")
    assert groups[0].anchor_cue_index == 2
    assert groups[0].anchor_lang == "en"


def test_within_cue_bilingual_lines_choose_matching_language(tmp_path):
    doc = _write(tmp_path, (
        "1\n00:00:01,000 --> 00:00:03,000\n你好\nHello\n"
    ))
    groups = group_bilingual(doc, "zh")
    assert groups == []
    assert doc.cues[0].anchor_text == "你好"
    doc_en = _write(tmp_path, (
        "1\n00:00:01,000 --> 00:00:03,000\n你好\nHello\n"
    ))
    group_bilingual(doc_en, "en")
    assert doc_en.cues[0].anchor_text == "hello"
