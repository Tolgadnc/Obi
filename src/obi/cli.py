"""The `obi` command: build, serve or check-videos."""

import argparse
import sys
from pathlib import Path

from .content import ContentError, load_content
from .serve import serve
from .site import build
from .videos import check_all, report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="obi", description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("data"), help="data folder (./data)")
    commands = parser.add_subparsers(dest="command", required=True)

    build_cmd = commands.add_parser("build", help="check the data and write the site")
    build_cmd.add_argument("--out", type=Path, default=Path("_site"), help="output (./_site)")
    build_cmd.add_argument(
        "--draft", action="store_true", help="allow techniques without an approved video"
    )

    serve_cmd = commands.add_parser("serve", help="preview locally, rebuilding on every change")
    serve_cmd.add_argument("--out", type=Path, default=Path("_site"), help="output (./_site)")
    serve_cmd.add_argument("--port", type=int, default=8000)
    serve_cmd.add_argument(
        "--strict", action="store_true", help="require a video for every technique, like CI"
    )

    check_cmd = commands.add_parser("check-videos", help="check every video on YouTube")
    check_cmd.add_argument("--report", type=Path, help="also write the report to this file")

    args = parser.parse_args(argv)
    try:
        if args.command == "build":
            return _build(args)
        if args.command == "serve":
            serve(args.data, args.out, args.port, strict=args.strict)
            return 0
        return _check_videos(args)
    except ContentError as error:
        print("\n".join(error.problems), file=sys.stderr)
        print(f"\n{error}", file=sys.stderr)
        return 1


def _build(args: argparse.Namespace) -> int:
    content = load_content(args.data, strict=not args.draft)
    for warning in content.warnings:
        print(f"warning: {warning}", file=sys.stderr)
    pages = build(content, args.out, draft=args.draft)
    print(f"Built {pages} pages in {args.out}")
    return 0


def _check_videos(args: argparse.Namespace) -> int:
    results = check_all(load_content(args.data, strict=False))
    text = report(results)
    print(text, end="")
    if args.report:
        args.report.write_text(text, encoding="utf-8")
    # Only approved videos are live on the site, so only they fail the check.
    return 1 if any(result.broken and result.video.approved for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
