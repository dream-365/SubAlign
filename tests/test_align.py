from subalign.align import align
from subalign.subtitle import group_bilingual
from subalign.subtitle.model import AsrToken, SubtitleCue, SubtitleDocument
from subalign.subtitle.normalize import normalize_text


def _doc(texts, starts):
    cues = []
    for index, (text, start) in enumerate(zip(texts, starts), start=1):
        normalized = normalize_text(text)
        cues.append(SubtitleCue(index, start, start + 1.0, text,
                                normalized=normalized, anchor_text=normalized, lang="zh"))
    return SubtitleDocument("srt", cues, [], "utf-8", False)


def test_aligns_shifted_cue_to_tokens():
    tokens = [
        AsrToken("你好", 0.0, 0.5, 0.9),
        AsrToken("世界", 0.5, 1.0, 0.9),
        AsrToken("这是", 2.0, 2.5, 0.9),
        AsrToken("测试", 2.5, 3.0, 0.9),
    ]
    doc = _doc(["你好世界", "这是测试"], [0.1, 4.0])
    groups = group_bilingual(doc, "zh")
    anchors = align(doc, groups, tokens, max_offset=60)
    assert [anchor.cue_index for anchor in anchors] == [1, 2]
    assert anchors[0].audio_start == 0.0
    assert anchors[0].audio_end == 1.0
    assert anchors[0].confidence == "high"
    assert anchors[1].audio_start == 2.0
    assert anchors[1].audio_end == 3.0


def test_unrelated_text_returns_no_anchor():
    tokens = [AsrToken("你好", 0.0, 1.0, 0.9)]
    doc = _doc(["完全不同的内容"], [10.0])
    assert align(doc, [], tokens) == []


def test_empty_tokens_returns_empty():
    doc = _doc(["你好"], [0.0])
    assert align(doc, [], []) == []


def test_bilingual_group_aligns_anchor_only():
    tokens = [AsrToken("你好", 0.0, 1.0, 0.9)]
    doc = _doc(["你好", "Hello"], [0.0, 0.0])
    doc.cues[0].lang = "zh"
    doc.cues[1].lang = "en"
    groups = group_bilingual(doc, "zh")
    anchors = align(doc, groups, tokens)
    assert len(anchors) == 1
    assert anchors[0].cue_index == 1
    assert anchors[0].group_id == 1
