"""Command-line contract for SubAlign."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .errors import InputInvalid, SubAlignError
from .pipeline import run


class _Parser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # type: ignore[override]
        raise InputInvalid(message)


def _build_parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="subalign", description="Align subtitle timelines to a video's audio track")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    align = subparsers.add_parser("align", help="correct subtitle timestamps")
    align.add_argument("--video", required=True)
    align.add_argument("--subtitle", required=True)
    align.add_argument("--out", required=True)
    align.add_argument("--report", default=None)
    align.add_argument("--lang", default="auto")
    align.add_argument("--model", default="large-v3-turbo")
    align.add_argument("--max-offset", type=float, default=60.0)
    align.add_argument("--shift", type=float, default=0.0,
                       help="seconds added after model correction; positive means later subtitles")
    align.add_argument("--dry-run", action="store_true")
    align.add_argument("--force", action="store_true")
    align.add_argument("--keep-temp", action="store_true")
    return parser


def _validate(args: argparse.Namespace) -> None:
    video = Path(args.video)
    subtitle = Path(args.subtitle)
    out = Path(args.out)
    if not video.is_file():
        raise InputInvalid("视频文件不存在", detail=str(video))
    if not subtitle.is_file():
        raise InputInvalid("字幕文件不存在", detail=str(subtitle))
    if args.max_offset <= 0:
        raise InputInvalid("--max-offset 必须为正数")
    if out.resolve() == subtitle.resolve() or out.resolve() == video.resolve():
        raise InputInvalid("--out 不能与输入文件相同")
    if subtitle.suffix.lower() not in (".srt", ".ass", ".ssa"):
        raise InputInvalid("不支持的字幕扩展名", detail=subtitle.suffix)
    if out.suffix.lower() != subtitle.suffix.lower():
        raise InputInvalid(
            "输出扩展名必须与输入格式一致",
            detail=f"{subtitle.suffix} -> {out.suffix}",
        )
    if out.exists() and not args.force:
        from .errors import OutputExists
        raise OutputExists("输出文件已存在", detail=str(out))


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
        if args.command != "align":
            raise InputInvalid("未知子命令", detail=args.command)
        _validate(args)
        report = run(
            args.video, args.subtitle, args.out,
            lang=args.lang, model=args.model, max_offset=args.max_offset,
            shift=args.shift,
            dry_run=args.dry_run, force=args.force, keep_temp=args.keep_temp,
            report_path=args.report,
        )
        action = "dry-run" if args.dry_run else "wrote"
        print(
            f"{action}: {args.out} | model={report['model']['kind']} "
            f"| coverage={report['coverage']:.1%} | report={args.report or args.out + '.report.json'}"
        )
        return 0
    except SubAlignError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERR_INTERNAL: {exc}", file=sys.stderr)
        return 6
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
