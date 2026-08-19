#!/usr/bin/env python3
"""Extract the original book's embedded images for the reviewed PDF builder."""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source_pdf", type=Path, help="A legally obtained copy of the source PDF")
    parser.add_argument("--output-dir", type=Path, default=Path("assets/source_images"))
    parser.add_argument("--expected-count", type=int, default=34)
    parser.add_argument("--force", action="store_true", help="Replace an existing figure extraction")
    args = parser.parse_args()

    source_pdf = args.source_pdf.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    if not source_pdf.is_file():
        raise FileNotFoundError(source_pdf)
    if not shutil.which("pdfimages"):
        raise RuntimeError("pdfimages is required. Install Poppler, then run this command again.")

    existing = sorted(output_dir.glob("figure-*")) if output_dir.exists() else []
    if existing and not args.force:
        raise FileExistsError(
            f"{output_dir} already contains extracted figures. Use --force to replace them."
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    if args.force:
        for path in existing:
            if path.is_file():
                path.unlink()

    subprocess.run(
        ["pdfimages", "-png", str(source_pdf), str(output_dir / "figure")],
        check=True,
    )
    figures = sorted(output_dir.glob("figure-*.png"))
    if len(figures) != args.expected_count:
        raise RuntimeError(
            f"Expected {args.expected_count} PNG images, but extracted {len(figures)}. "
            "Confirm that this is the same source edition."
        )
    print(f"Extracted {len(figures)} images to {output_dir}")


if __name__ == "__main__":
    main()
