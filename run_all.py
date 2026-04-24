from __future__ import annotations

import sys

from pipeline import main as pipeline_main


def main(argv: list[str] | None = None) -> int:
    if argv is None:
        argv = sys.argv[1:]
    args = ["--run-all-default-pairs"]
    args.extend(argv)
    return pipeline_main(args)


if __name__ == "__main__":
    raise SystemExit(main())
