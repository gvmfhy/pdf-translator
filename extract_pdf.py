#!/usr/bin/env python3
"""
PDF Text Extraction and Chunking Tool
Extracts text from PDFs and splits into manageable chunks for translation.

Author: Austin Morrissey
Co-Authored-By: Claude <noreply@anthropic.com>
"""

import json
import PyPDF2
from pathlib import Path
import argparse
import sys


class PDFExtractor:
    """Handles PDF text extraction and chunking."""

    def __init__(self, pdf_path, output_dir, chunk_size=20):
        """
        Initialize the PDF extractor.

        Args:
            pdf_path: Path to the PDF file
            output_dir: Directory to save chunks
            chunk_size: Number of pages per chunk
        """
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.chunk_size = chunk_size
        self.chunks_dir = self.output_dir / 'chunks'
        self.progress_file = self.output_dir / 'progress.json'

        # Create directories
        self.chunks_dir.mkdir(parents=True, exist_ok=True)

    def extract_metadata(self):
        """Extract PDF metadata."""
        with open(self.pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            metadata = {
                'total_pages': len(reader.pages),
                'title': None,
                'author': None,
            }

            if reader.metadata:
                metadata['title'] = reader.metadata.get('/Title', None)
                metadata['author'] = reader.metadata.get('/Author', None)

            return metadata

    def extract_page(self, reader, page_num):
        """Extract text from a single page."""
        try:
            page = reader.pages[page_num]
            text = page.extract_text()
            return text.strip()
        except Exception as e:
            print(f"Warning: Error extracting page {page_num + 1}: {e}")
            return ""

    def create_chunk(self, reader, start_page, end_page, chunk_num):
        """
        Extract and save a chunk of pages.

        Args:
            reader: PyPDF2 reader object
            start_page: Starting page number (0-indexed)
            end_page: Ending page number (0-indexed, inclusive)
            chunk_num: Chunk number for filename
        """
        chunk_text = []

        # Add header
        chunk_text.append(f"# Pages {start_page + 1}-{end_page + 1}")
        chunk_text.append(f"# Chunk {chunk_num}")
        chunk_text.append("=" * 80)
        chunk_text.append("")

        # Extract pages
        for page_num in range(start_page, end_page + 1):
            text = self.extract_page(reader, page_num)

            if text:
                chunk_text.append(f"[PAGE {page_num + 1}]")
                chunk_text.append(text)
                chunk_text.append("")
                chunk_text.append("-" * 80)
                chunk_text.append("")

        # Save chunk
        filename = f"chunk_{chunk_num:03d}_pages_{start_page + 1:03d}_{end_page + 1:03d}.txt"
        filepath = self.chunks_dir / filename

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(chunk_text))

        return {
            'chunk_num': chunk_num,
            'filename': filename,
            'start_page': start_page + 1,
            'end_page': end_page + 1,
            'page_count': end_page - start_page + 1,
            'translated': False
        }

    def extract_all(self, start_page=0):
        """
        Extract all pages from PDF into chunks.

        Args:
            start_page: Starting page number (0-indexed)
        """
        print(f"Opening PDF: {self.pdf_path}")

        with open(self.pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total_pages = len(reader.pages)

            print(f"Total pages: {total_pages}")
            print(f"Chunk size: {self.chunk_size} pages")

            # Extract metadata
            metadata = self.extract_metadata()
            if metadata['title']:
                print(f"Title: {metadata['title']}")
            if metadata['author']:
                print(f"Author: {metadata['author']}")

            print(f"\nExtracting chunks...")
            print("=" * 80)

            chunks = []
            chunk_num = 1
            current_page = start_page

            while current_page < total_pages:
                end_page = min(current_page + self.chunk_size - 1, total_pages - 1)

                print(f"Chunk {chunk_num}: Pages {current_page + 1}-{end_page + 1}")

                chunk_info = self.create_chunk(reader, current_page, end_page, chunk_num)
                chunks.append(chunk_info)

                current_page = end_page + 1
                chunk_num += 1

            # Save progress
            progress = {
                'pdf_file': str(self.pdf_path),
                'metadata': metadata,
                'chunk_size': self.chunk_size,
                'total_chunks': len(chunks),
                'chunks': chunks
            }

            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(progress, f, indent=2, ensure_ascii=False)

            print("=" * 80)
            print(f"\n✓ Extraction complete!")
            print(f"  Total chunks created: {len(chunks)}")
            print(f"  Chunks directory: {self.chunks_dir}")
            print(f"  Progress file: {self.progress_file}")
            print(f"\nNext step: Use Claude Code to translate chunks")
            print(f'  Example: "translate chunk 1"')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Extract and chunk PDF text for translation'
    )
    parser.add_argument(
        'pdf_file',
        help='Path to PDF file'
    )
    parser.add_argument(
        '--output-dir',
        default='~/pdf-translator',
        help='Output directory (default: ~/pdf-translator)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=20,
        help='Pages per chunk (default: 20)'
    )
    parser.add_argument(
        '--start-page',
        type=int,
        default=1,
        help='Starting page number (default: 1)'
    )

    args = parser.parse_args()

    # Expand paths
    pdf_path = Path(args.pdf_file).expanduser()
    output_dir = Path(args.output_dir).expanduser()

    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Create extractor and run
    extractor = PDFExtractor(
        pdf_path=pdf_path,
        output_dir=output_dir,
        chunk_size=args.chunk_size
    )

    extractor.extract_all(start_page=args.start_page - 1)


if __name__ == '__main__':
    main()
