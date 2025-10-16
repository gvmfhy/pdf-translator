#!/usr/bin/env python3
"""
Translation Assembly Tool
Combines translated chunks into final output formats.

Author: Austin Morrissey
Co-Authored-By: Claude <noreply@anthropic.com>
"""

import json
from pathlib import Path
import argparse
import sys
from datetime import datetime


class TranslationAssembler:
    """Assembles translated chunks into final documents."""

    def __init__(self, project_dir):
        """Initialize the assembler."""
        self.project_dir = Path(project_dir).expanduser()
        self.translations_dir = self.project_dir / 'translations'
        self.output_dir = self.project_dir / 'output'
        self.progress_file = self.project_dir / 'progress.json'

        # Create output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load progress
        if not self.progress_file.exists():
            print(f"Error: Progress file not found: {self.progress_file}", file=sys.stderr)
            sys.exit(1)

        with open(self.progress_file, 'r', encoding='utf-8') as f:
            self.progress = json.load(f)

    def get_translation_status(self):
        """Check which chunks have been translated."""
        translated = []
        missing = []

        for chunk in self.progress['chunks']:
            chunk_num = chunk['chunk_num']
            # Check for corresponding translation file
            trans_file = self.translations_dir / f"chunk_{chunk_num:03d}_translation.md"

            if trans_file.exists():
                translated.append(chunk_num)
            else:
                missing.append(chunk_num)

        return translated, missing

    def assemble_markdown(self, output_file=None):
        """Assemble all translations into a single markdown file."""
        if output_file is None:
            title = self.progress['metadata'].get('title', 'translation')
            # Clean filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:50]
            output_file = self.output_dir / f"{safe_title}_english.md"

        translated, missing = self.get_translation_status()

        if missing:
            print(f"Warning: {len(missing)} chunks not yet translated: {missing}")
            print(f"Assembling {len(translated)} available chunks...")

        # Build document
        content = []

        # Header
        metadata = self.progress['metadata']
        content.append(f"# {metadata.get('title', 'Untitled')}")
        content.append(f"## {metadata.get('author', 'Unknown Author')}")
        content.append("")
        content.append(f"**English Translation**")
        content.append(f"*Translated: {datetime.now().strftime('%B %d, %Y')}*")
        content.append("")
        content.append("---")
        content.append("")

        # Assemble chunks in order
        for chunk in self.progress['chunks']:
            chunk_num = chunk['chunk_num']
            trans_file = self.translations_dir / f"chunk_{chunk_num:03d}_translation.md"

            if trans_file.exists():
                with open(trans_file, 'r', encoding='utf-8') as f:
                    chunk_content = f.read().strip()

                # Add chunk
                content.append(chunk_content)
                content.append("")
                content.append("")
            else:
                # Placeholder for missing chunks
                content.append(f"<!-- CHUNK {chunk_num} NOT YET TRANSLATED -->")
                content.append(f"<!-- Pages {chunk['start_page']}-{chunk['end_page']} -->")
                content.append("")

        # Write output
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

        print(f"✓ Markdown assembled: {output_file}")
        print(f"  Chunks included: {len(translated)}/{len(self.progress['chunks'])}")

        return output_file

    def create_html(self, markdown_file, output_file=None):
        """Create styled HTML version (requires markdown library)."""
        try:
            import markdown
        except ImportError:
            print("Note: Install 'markdown' package to generate HTML")
            print("  pip3 install markdown")
            return None

        if output_file is None:
            output_file = markdown_file.with_suffix('.html')

        # Read markdown
        with open(markdown_file, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # Convert to HTML
        html_content = markdown.markdown(md_content, extensions=['extra', 'codehilite'])

        # Wrap in styled template
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.progress['metadata'].get('title', 'Translation')}</title>
    <style>
        body {{
            font-family: 'Georgia', 'Times New Roman', serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background-color: #fafafa;
            color: #333;
        }}
        h1 {{
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            color: #1a1a1a;
        }}
        h2 {{
            font-size: 1.8rem;
            margin-top: 2rem;
            color: #2a2a2a;
        }}
        h3 {{
            font-size: 1.4rem;
            margin-top: 1.5rem;
            color: #3a3a3a;
        }}
        p {{
            margin-bottom: 1rem;
            text-align: justify;
        }}
        hr {{
            border: none;
            border-top: 2px solid #ddd;
            margin: 2rem 0;
        }}
        blockquote {{
            border-left: 4px solid #ccc;
            margin-left: 0;
            padding-left: 1.5rem;
            color: #555;
            font-style: italic;
        }}
        @media (prefers-color-scheme: dark) {{
            body {{
                background-color: #1a1a1a;
                color: #e0e0e0;
            }}
            h1, h2, h3 {{
                color: #f0f0f0;
            }}
        }}
        @media print {{
            body {{
                background-color: white;
                color: black;
            }}
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

        # Write HTML
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_template)

        print(f"✓ HTML created: {output_file}")

        return output_file

    def show_status(self):
        """Display current translation status."""
        translated, missing = self.get_translation_status()

        print("=" * 80)
        print("TRANSLATION STATUS")
        print("=" * 80)
        print(f"PDF: {self.progress['metadata'].get('title', 'Unknown')}")
        print(f"Total pages: {self.progress['metadata']['total_pages']}")
        print(f"Total chunks: {len(self.progress['chunks'])}")
        print(f"Translated: {len(translated)}/{len(self.progress['chunks'])} chunks")
        print(f"Progress: {len(translated) / len(self.progress['chunks']) * 100:.1f}%")
        print("")

        if missing:
            print(f"Remaining chunks: {missing}")
        else:
            print("✓ All chunks translated!")

        print("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Assemble translated chunks into final output'
    )
    parser.add_argument(
        '--project-dir',
        default='~/pdf-translator',
        help='Project directory (default: ~/pdf-translator)'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show translation status only'
    )
    parser.add_argument(
        '--format',
        choices=['markdown', 'html', 'both'],
        default='both',
        help='Output format (default: both)'
    )

    args = parser.parse_args()

    assembler = TranslationAssembler(args.project_dir)

    if args.status:
        assembler.show_status()
        return

    # Generate outputs
    if args.format in ['markdown', 'both']:
        md_file = assembler.assemble_markdown()

        if args.format == 'both':
            assembler.create_html(md_file)

    elif args.format == 'html':
        md_file = assembler.assemble_markdown()
        assembler.create_html(md_file)

    print("\n✓ Assembly complete!")


if __name__ == '__main__':
    main()
