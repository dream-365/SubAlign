from pathlib import Path

import pytest

from subalign.io.writer import write_subtitle
from subalign.subtitle import parse_subtitle
from subalign.subtitle.model import CueAdjustment

FIXTURES = sorted(Path(__file__).parent.joinpath("fixtures").glob("*.srt")) + sorted(
    Path(__file__).parent.joinpath("fixtures").glob("*.ass")
)


@pytest.mark.parametrize("path", FIXTURES, ids=[path.name for path in FIXTURES])
def test_fixture_parses_and_roundtrips_without_time_changes(path: Path, tmp_path: Path):
    doc = parse_subtitle(path)
    assert len(doc.cues) >= 4
    assert doc.format == path.suffix.lstrip(".")
    adjustments = [
        CueAdjustment(cue.index, 0.0, 0.0, cue.start, cue.end, "high", 0)
        for cue in doc.cues
    ]
    out = tmp_path / path.name
    write_subtitle(doc, adjustments, out)
    assert out.read_bytes() == path.read_bytes()
