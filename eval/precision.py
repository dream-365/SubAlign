"""Compare predicted subtitle timings against a hand-checked truth file."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from subalign.subtitle import parse_subtitle  # noqa: E402


def percentile(values: list[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def _stats(values: list[float]) -> dict:
    if not values:
        return {"count": 0, "median": None, "p90": None, "max": None}
    ordered = sorted(values)
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2
    return {
        "count": len(ordered),
        "median": round(median, 4),
        "p90": round(percentile(ordered, 0.9), 4),
        "max": round(ordered[-1], 4),
    }


def compare_documents(truth, predicted) -> dict:
    truth_by_index = {cue.index: cue for cue in truth.cues}
    start_errors: list[float] = []
    end_errors: list[float] = []
    by_lang: dict[str, dict[str, list[float]]] = {}
    for cue in predicted.cues:
        reference = truth_by_index.get(cue.index)
        if reference is None:
            continue
        start_error = abs(cue.start - reference.start)
        end_error = abs(cue.end - reference.end)
        start_errors.append(start_error)
        end_errors.append(end_error)
        bucket = by_lang.setdefault(reference.lang, {"start": [], "end": []})
        bucket["start"].append(start_error)
        bucket["end"].append(end_error)
    return {
        "format": predicted.format,
        "cues": len(predicted.cues),
        "matched": len(start_errors),
        "start": _stats(start_errors),
        "end": _stats(end_errors),
        "by_lang": {
            lang: {"start": _stats(values["start"]), "end": _stats(values["end"])}
            for lang, values in sorted(by_lang.items())
        },
    }


def _find_pairs(root: Path) -> list[tuple[str, Path, Path]]:
    pairs = []
    for truth in sorted(root.rglob("truth.*")):
        suffix = truth.suffix
        predicted = truth.with_name(f"pred{suffix}")
        if predicted.exists():
            pairs.append((truth.parent.name, truth, predicted))
    return pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", help="directory containing <case>/truth.* and <case>/pred.*")
    parser.add_argument("--truth")
    parser.add_argument("--pred")
    parser.add_argument("--out")
    args = parser.parse_args(argv)

    pairs: list[tuple[str, Path, Path]] = []
    if args.truth and args.pred:
        pairs.append(("single", Path(args.truth), Path(args.pred)))
    elif args.fixtures:
        pairs = _find_pairs(Path(args.fixtures))
    else:
        parser.error("provide --fixtures or --truth/--pred")

    results = []
    all_start: list[float] = []
    all_end: list[float] = []
    for name, truth_path, pred_path in pairs:
        truth = parse_subtitle(truth_path)
        predicted = parse_subtitle(pred_path)
        result = compare_documents(truth, predicted)
        result["case"] = name
        results.append(result)
        truth_by_index = {cue.index: cue for cue in truth.cues}
        for cue in predicted.cues:
            reference = truth_by_index.get(cue.index)
            if reference is not None:
                all_start.append(abs(cue.start - reference.start))
                all_end.append(abs(cue.end - reference.end))

    payload = {
        "pairs": results,
        "overall": {"start": _stats(all_start), "end": _stats(all_end)},
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
