"""Command-line entry point for the electricity VAT cut pipeline.

Exposes a :func:`main` callable that ``[project.scripts]`` registers as
``electricity-vat-cut-build`` and that ``__main__.py`` invokes for
``python -m electricity_vat_cut``.

All defaults come from :mod:`electricity_vat_cut.sources`, where each value
carries a description and a source URL.
"""

from __future__ import annotations

import argparse

from .sources import PASS_THROUGH_SCENARIOS, WINTER_SHARE


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="electricity-vat-cut-build",
        description="Generate dashboard-ready electricity VAT cut results.",
    )
    parser.add_argument("--year", type=int, default=2026)
    parser.add_argument(
        "--data-folder",
        default=None,
        help=(
            "Folder for the per-year Enhanced FRS dataset files (default "
            "data/policyengine_datasets inside the repo). Point at an "
            "existing folder to reuse already-materialised datasets."
        ),
    )
    parser.add_argument(
        "--winter-share",
        type=float,
        default=WINTER_SHARE.value,
        help=WINTER_SHARE.description,
    )
    parser.add_argument(
        "--pass-through",
        type=float,
        nargs="+",
        default=[s.value for s in PASS_THROUGH_SCENARIOS],
        help="Pass-through scenarios; see sources.PASS_THROUGH_SCENARIOS for citations.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    from .pipeline import run

    run(
        year=args.year,
        data_folder=args.data_folder,
        winter_share=args.winter_share,
        pass_through=args.pass_through,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
