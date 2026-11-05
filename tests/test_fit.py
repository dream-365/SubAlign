import random

from subalign.fit import apply_model, select_model
from subalign.subtitle import group_bilingual
from subalign.subtitle.model import Anchor, OffsetModel, SubtitleCue, SubtitleDocument


def _doc(count=60):
    cues = [SubtitleCue(index=i + 1, start=i * 10.0, end=i * 10.0 + 3.0,
                        text=f"line {i}", lang="zh") for i in range(count)]
    return SubtitleDocument("srt", cues, [], "utf-8", False)


def _anchors(doc, fn, noise=0.02, seed=1):
    rng = random.Random(seed)
    anchors = []
    for cue in doc.cues:
        value = fn(cue.start) + rng.gauss(0, noise)
        anchors.append(Anchor(cue.index, 0, cue.start + value, cue.end + value, 0.95, "high"))
    return anchors


def test_constant_model():
    doc = _doc()
    model, ambiguous, _ = select_model(_anchors(doc, lambda t: 2.0), doc.cues)
    assert model.kind == "constant"
    assert abs(model.intercept - 2.0) < 0.05
    assert ambiguous is False


def test_linear_model():
    doc = _doc()
    model, _, _ = select_model(_anchors(doc, lambda t: 0.5 + 0.0004 * t), doc.cues)
    assert model.kind == "linear"
    assert abs(model.slope - 0.0004) < 0.0001


def test_piecewise_model_detects_breakpoint():
    doc = _doc()
    model, _, _ = select_model(_anchors(doc, lambda t: 2.0 if t < 300 else 4.0), doc.cues)
    assert model.kind == "piecewise"
    assert len(model.breakpoints) == 1
    assert abs(model.breakpoints[0] - 300.0) < 10.0


def test_apply_model_clamps_negative_start():
    doc = _doc(1)
    model = OffsetModel("constant", intercept=-5.0, segment_offsets=[-5.0])
    adjustments, coverage, warnings = apply_model(doc, model, [], [])
    assert adjustments[0].final_start == 0.0
    assert adjustments[0].final_end > adjustments[0].final_start
    assert adjustments[0].final_end - adjustments[0].final_start == doc.cues[0].end - doc.cues[0].start
    assert any(item.startswith("WARN_CLAMPED") for item in warnings)
    assert coverage == 0.0


def test_robust_piecewise_handles_outlier_anchors():
    doc = _doc(60)
    anchors = []
    for index, cue in enumerate(doc.cues):
        offset = 2.0 if cue.start < 300 else 5.0
        if index % 9 == 0:
            offset += 25.0
        anchors.append(Anchor(cue.index, 0, cue.start + offset,
                              cue.end + offset, 0.95, "high"))
    model, ambiguous, _ = select_model(anchors, doc.cues)
    assert model.kind == "piecewise"
    assert len(model.breakpoints) >= 1
    assert model.rmse < 2.0
    assert ambiguous is False


def test_outlier_anchor_does_not_override_model_prediction():
    doc = _doc(2)
    anchors = [
        Anchor(1, 0, doc.cues[0].start + 2.0, doc.cues[0].end + 2.0, 0.95, "high"),
        Anchor(2, 0, doc.cues[1].start + 20.0, doc.cues[1].end + 20.0, 0.95, "high"),
    ]
    model = OffsetModel("constant", intercept=2.0, segment_offsets=[2.0])
    adjustments, _, _ = apply_model(doc, model, anchors, [])
    assert adjustments[0].delta_start == 2.0
    assert adjustments[1].delta_start == 2.0


def test_coverage_counts_group_cues():
    doc = _doc(2)
    doc.cues[0].text = "你好"
    doc.cues[1].text = "Hello"
    doc.cues[0].lang = "zh"
    doc.cues[1].lang = "en"
    doc.cues[1].start = doc.cues[0].start
    doc.cues[1].end = doc.cues[0].end
    groups = group_bilingual(doc, "zh")
    anchors = [Anchor(1, 1, doc.cues[0].start + 1.0, doc.cues[0].end + 1.0, 0.95, "high")]
    model = OffsetModel("constant", intercept=1.0, segment_offsets=[1.0])
    adjustments, coverage, _ = apply_model(doc, model, anchors, groups)
    assert coverage == 1.0
    assert adjustments[0].delta_start == adjustments[1].delta_start
    assert adjustments[1].anchor_lang == "none"
