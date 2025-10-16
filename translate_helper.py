#!/usr/bin/env python3
"""
Translation Workflow Helper
Assists with managing the Claude Code translation workflow.

Author: Austin Morrissey
Co-Authored-By: Claude <noreply@anthropic.com>
"""

import json
from pathlib import Path
import argparse
import sys


class TranslationHelper:
    """Helper for translation workflow."""

    def __init__(self, project_dir):
        """Initialize the helper."""
        self.project_dir = Path(project_dir).expanduser()
        self.chunks_dir = self.project_dir / 'chunks'
        self.translations_dir = self.project_dir / 'translations'
        self.progress_file = self.project_dir / 'progress.json'

        # Create translations directory
        self.translations_dir.mkdir(parents=True, exist_ok=True)

        # Load progress
        if not self.progress_file.exists():
            print(f"Error: Progress file not found: {self.progress_file}", file=sys.stderr)
            print(f"Run extract_pdf.py first!", file=sys.stderr)
            sys.exit(1)

        with open(self.progress_file, 'r', encoding='utf-8') as f:
            self.progress = json.load(f)

    def get_next_chunk(self):
        """Find the next untranslated chunk."""
        for chunk in self.progress['chunks']:
            chunk_num = chunk['chunk_num']
            trans_file = self.translations_dir / f"chunk_{chunk_num:03d}_translation.md"

            if not trans_file.exists():
                return chunk

        return None

    def get_chunk(self, chunk_num):
        """Get a specific chunk by number."""
        for chunk in self.progress['chunks']:
            if chunk['chunk_num'] == chunk_num:
                return chunk
        return None

    def read_chunk_source(self, chunk_num):
        """Read the source text for a chunk."""
        chunk = self.get_chunk(chunk_num)
        if not chunk:
            return None

        chunk_file = self.chunks_dir / chunk['filename']
        if not chunk_file.exists():
            return None

        with open(chunk_file, 'r', encoding='utf-8') as f:
            return f.read()

    def show_chunk(self, chunk_num):
        """Display a chunk for translation."""
        chunk = self.get_chunk(chunk_num)
        if not chunk:
            print(f"Error: Chunk {chunk_num} not found", file=sys.stderr)
            return False

        print("=" * 80)
        print(f"CHUNK {chunk_num} - Pages {chunk['start_page']}-{chunk['end_page']}")
        print("=" * 80)

        # Check if already translated
        trans_file = self.translations_dir / f"chunk_{chunk_num:03d}_translation.md"
        if trans_file.exists():
            print(f"⚠️  This chunk already has a translation at:")
            print(f"   {trans_file}")
            print()

        # Read and display source
        source = self.read_chunk_source(chunk_num)
        if source:
            print(source)
            print()
            print("=" * 80)
            print("Ready to translate the above text.")
            print(f"Save translation to: {trans_file}")
            print("=" * 80)
        else:
            print(f"Error: Could not read chunk file", file=sys.stderr)
            return False

        return True

    def show_next(self):
        """Show the next untranslated chunk."""
        chunk = self.get_next_chunk()

        if not chunk:
            print("✓ All chunks have been translated!")
            print("Run 'python assemble_output.py' to create final output.")
            return False

        return self.show_chunk(chunk['chunk_num'])

    def mark_translated(self, chunk_num):
        """Mark a chunk as translated in progress file."""
        for chunk in self.progress['chunks']:
            if chunk['chunk_num'] == chunk_num:
                chunk['translated'] = True
                break

        with open(self.progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.progress, f, indent=2, ensure_ascii=False)

    def show_status(self):
        """Show overall translation status."""
        translated_count = 0
        total_chunks = len(self.progress['chunks'])

        for chunk in self.progress['chunks']:
            chunk_num = chunk['chunk_num']
            trans_file = self.translations_dir / f"chunk_{chunk_num:03d}_translation.md"
            if trans_file.exists():
                translated_count += 1

        print("=" * 80)
        print("TRANSLATION PROGRESS")
        print("=" * 80)
        print(f"Book: {self.progress['metadata'].get('title', 'Unknown')}")
        print(f"Total pages: {self.progress['metadata']['total_pages']}")
        print(f"Total chunks: {total_chunks}")
        print(f"Translated: {translated_count}/{total_chunks}")
        print(f"Progress: {translated_count / total_chunks * 100:.1f}%")
        print()

        # Show list of chunks
        for chunk in self.progress['chunks']:
            chunk_num = chunk['chunk_num']
            trans_file = self.translations_dir / f"chunk_{chunk_num:03d}_translation.md"
            status = "✓" if trans_file.exists() else "○"
            print(f"  {status} Chunk {chunk_num:2d}: Pages {chunk['start_page']:3d}-{chunk['end_page']:3d}")

        print("=" * 80)

        next_chunk = self.get_next_chunk()
        if next_chunk:
            print(f"\nNext to translate: Chunk {next_chunk['chunk_num']} (pages {next_chunk['start_page']}-{next_chunk['end_page']})")
            print(f"Use: python translate_helper.py --next")
        else:
            print("\n✓ All chunks translated!")
            print("Run: python assemble_output.py")

    def create_translation_template(self, chunk_num):
        """Create a template file for translation."""
        chunk = self.get_chunk(chunk_num)
        if not chunk:
            print(f"Error: Chunk {chunk_num} not found", file=sys.stderr)
            return None

        trans_file = self.translations_dir / f"chunk_{chunk_num:03d}_translation.md"

        # Create template
        template = f"""<!-- Translation of Chunk {chunk_num}: Pages {chunk['start_page']}-{chunk['end_page']} -->
<!-- Original: {chunk['filename']} -->

# [TRANSLATION GOES HERE]

<!-- Save this file when translation is complete -->
"""

        with open(trans_file, 'w', encoding='utf-8') as f:
            f.write(template)

        print(f"✓ Created translation template: {trans_file}")
        return trans_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Translation workflow helper'
    )
    parser.add_argument(
        '--project-dir',
        default='~/pdf-translator',
        help='Project directory (default: ~/pdf-translator)'
    )
    parser.add_argument(
        '--next',
        action='store_true',
        help='Show next untranslated chunk'
    )
    parser.add_argument(
        '--chunk',
        type=int,
        help='Show specific chunk number'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show translation status'
    )

    args = parser.parse_args()

    helper = TranslationHelper(args.project_dir)

    if args.status:
        helper.show_status()
    elif args.next:
        helper.show_next()
    elif args.chunk:
        helper.show_chunk(args.chunk)
    else:
        # Default: show status
        helper.show_status()


if __name__ == '__main__':
    main()
