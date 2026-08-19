#!/usr/bin/env python3
"""Run strict structural checks on the reviewed translation and built PDF."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import unicodedata
from pathlib import Path

from pypdf import PdfReader

EXPECTED_CHUNKS = set(range(1, 15))
EXPECTED_IMAGE_ONLY_PAGES = {1, 132, 274}
EXPECTED_TITLE = "Networking for Spies: How to Benefit from Any Acquaintance"
EXPECTED_AUTHOR = "Elena Vavilova and Andrey Bezrukov"
SUSPICIOUS_PATTERNS = {
    "operative worker": re.compile(r"\boperative workers?\b", re.IGNORECASE),
    "development target": re.compile(r"\bdevelopment targets?\b", re.IGNORECASE),
    "broken OIS grammar": re.compile(
        r"\bis they (?:dangerous|interesting|difficult)\b", re.IGNORECASE
    ),
    "chunk marker": re.compile(
        r"\[(?:Continued from|End of Chunk|End of Book)", re.IGNORECASE
    ),
    "Cyrillic residue": re.compile(r"[А-Яа-яЁё]"),
}


def normalized_words(text: str, alphabet: str):
    return re.findall(alphabet, text)


def source_tokens(text: str):
    text = unicodedata.normalize(
        "NFKC", (text or "").replace("\u00ad", "").replace("`", "")
    )
    return re.findall(r"[^\W\d_]+|\d+", text.lower(), re.UNICODE)


def numbered_chunks(paths):
    numbered = {}
    invalid = []
    duplicates = []
    for path in paths:
        match = re.match(r"chunk_(\d{3})", path.name)
        if not match:
            invalid.append(path.name)
            continue
        chunk_number = int(match.group(1))
        if chunk_number in numbered:
            duplicates.append(chunk_number)
        numbered[chunk_number] = path
    return numbered, invalid, sorted(set(duplicates))


def inspect_project(project_dir: Path, source_pdf: Path):
    chunks = sorted((project_dir / "chunks").glob("chunk_*.txt"))
    translations = sorted(
        (project_dir / "translations").glob("chunk_*_translation.md")
    )
    source_by_number, invalid_source_names, duplicate_source_numbers = (
        numbered_chunks(chunks)
    )
    target_by_number, invalid_target_names, duplicate_target_numbers = (
        numbered_chunks(translations)
    )

    reader = PdfReader(str(source_pdf))
    page_markers = set()
    saved_pages = {}
    ratios = []
    translation_text = ""

    for source in chunks:
        source_text = source.read_text(encoding="utf-8")
        page_markers.update(
            map(
                int,
                re.findall(
                    r"^\[PAGE (\d+)\]", source_text, flags=re.MULTILINE
                ),
            )
        )
        parts = re.split(
            r"^\[PAGE (\d+)\]\n", source_text, flags=re.MULTILINE
        )
        for index in range(1, len(parts), 2):
            page_number = int(parts[index])
            saved_pages[page_number] = (
                parts[index + 1].split("\n\n" + "-" * 80, 1)[0].strip()
            )

    for translation in translations:
        translation_text += "\n" + translation.read_text(encoding="utf-8")

    paired_chunk_numbers = sorted(
        source_by_number.keys() & target_by_number.keys()
    )
    for chunk_number in paired_chunk_numbers:
        source_text = source_by_number[chunk_number].read_text(encoding="utf-8")
        target_text = target_by_number[chunk_number].read_text(encoding="utf-8")
        russian = len(normalized_words(source_text, r"[А-Яа-яЁё]+"))
        english = len(
            normalized_words(target_text, r"[A-Za-z]+(?:'[A-Za-z]+)?")
        )
        ratios.append(round(english / russian, 3) if russian else None)

    suspicious = {
        label: len(pattern.findall(translation_text))
        for label, pattern in SUSPICIOUS_PATTERNS.items()
    }
    token_differences = []
    for page_number, page in enumerate(reader.pages, start=1):
        live_tokens = source_tokens(page.extract_text() or "")
        saved_tokens = source_tokens(saved_pages.get(page_number, ""))
        if live_tokens != saved_tokens:
            token_differences.append(page_number)

    actual_source_chunks = set(source_by_number)
    actual_target_chunks = set(target_by_number)
    expected_chunk_sets_match = all(
        [
            actual_source_chunks == EXPECTED_CHUNKS,
            actual_target_chunks == EXPECTED_CHUNKS,
            not invalid_source_names,
            not invalid_target_names,
            not duplicate_source_numbers,
            not duplicate_target_numbers,
        ]
    )
    unmarked_pages = set(range(1, len(reader.pages) + 1)) - page_markers

    return {
        "source_pdf_pages": len(reader.pages),
        "source_chunks": len(chunks),
        "translation_chunks": len(translations),
        "source_chunk_numbers": sorted(actual_source_chunks),
        "translation_chunk_numbers": sorted(actual_target_chunks),
        "expected_chunk_sets_match": expected_chunk_sets_match,
        "missing_translation_chunks": sorted(
            EXPECTED_CHUNKS - actual_target_chunks
        ),
        "unexpected_translation_chunks": sorted(
            actual_target_chunks - EXPECTED_CHUNKS
        ),
        "invalid_chunk_filenames": {
            "source": invalid_source_names,
            "translation": invalid_target_names,
        },
        "duplicate_chunk_numbers": {
            "source": duplicate_source_numbers,
            "translation": duplicate_target_numbers,
        },
        "source_page_markers": len(page_markers),
        "source_pages_without_text_markers": sorted(unmarked_pages),
        "expected_image_only_pages_match": (
            unmarked_pages == EXPECTED_IMAGE_ONLY_PAGES
        ),
        "source_pages_with_token_differences": token_differences,
        "source_to_english_word_ratios": ratios,
        "suspicious_pattern_counts": suspicious,
    }


def inspect_pdf(pdf_path: Path):
    reader = PdfReader(str(pdf_path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    pdfinfo = subprocess.run(
        ["pdfinfo", str(pdf_path)],
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    required = [
        "Synopsis",
        "Preface. Intelligence Is Networking",
        "Introduction. Networking from a Spy's Perspective",
        *[f"Chapter {number}." for number in range(1, 9)],
        "Conclusion. Networking as Self-Improvement",
    ]
    wanted_pdfinfo = {
        "Pages",
        "Encrypted",
        "Page size",
        "File size",
        "PDF version",
    }
    return {
        "pages": len(reader.pages),
        "metadata_title": reader.metadata.title,
        "metadata_author": reader.metadata.author,
        "text_characters": len(text),
        "required_sections_present": {item: item in text for item in required},
        "forbidden_text": {
            "chunk_markers": bool(
                re.search(
                    r"End of Chunk|Continued from Chunk|End of Book",
                    text,
                    re.IGNORECASE,
                )
            ),
            "Cyrillic": bool(re.search(r"[А-Яа-яЁё]", text)),
            "non_ASCII_dashes": bool(
                re.search(r"[\u2011\u2012\u2013\u2014\u2212]", text)
            ),
        },
        "pdfinfo": {
            line.split(":", 1)[0]: line.split(":", 1)[1].strip()
            for line in pdfinfo.splitlines()
            if ":" in line and line.split(":", 1)[0] in wanted_pdfinfo
        },
    }


def project_checks_pass(project):
    return all(
        [
            project["source_pdf_pages"] == 274,
            project["expected_chunk_sets_match"],
            project["source_page_markers"] == 271,
            project["expected_image_only_pages_match"],
            not project["source_pages_with_token_differences"],
            not any(project["suspicious_pattern_counts"].values()),
        ]
    )


def pdf_checks_pass(pdf):
    return all(
        [
            pdf["pages"] == 137,
            pdf["metadata_title"] == EXPECTED_TITLE,
            pdf["metadata_author"] == EXPECTED_AUTHOR,
            all(pdf["required_sections_present"].values()),
            not any(pdf["forbidden_text"].values()),
        ]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-dir", type=Path, default=Path("."))
    parser.add_argument("--source-pdf", type=Path, required=True)
    parser.add_argument("--pdf", type=Path)
    args = parser.parse_args()

    report = {
        "project": inspect_project(
            args.project_dir.resolve(), args.source_pdf.resolve()
        )
    }
    if args.pdf:
        report["pdf"] = inspect_pdf(args.pdf.resolve())
    report["passed"] = project_checks_pass(report["project"]) and (
        "pdf" not in report or pdf_checks_pass(report["pdf"])
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if not report["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
