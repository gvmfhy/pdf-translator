# PDF Translation System

A semi-automated PDF translation system using Claude Code as the translation engine.


## 🎯 Project Highlight: "Networking for Spies"

This system was built to translate **"Нетворкинг для разведчиков"** — a 274-page **Russian Cyrillic book on intelligence tradecraft** written by **Elena Vavilova and Andrey Bezrukov**, two former Russian intelligence officers who operated undercover in the United States for over 20 years.

### About the Authors
The authors were among the "Illegals" exposed in the 2010 spy scandal and exchanged in the largest spy swap since the Cold War. Their book reveals professional networking techniques used in espionage operations, now adapted for business and personal development. This translation makes their unique intelligence perspective accessible to English readers.

### Translation Achievement
- ✅ **274 pages** of Russian Cyrillic text → English
- ✅ **14 chunks** processed systematically (20 pages each)
- ✅ **Literary quality** translation preserving spy terminology and author voice
- ✅ Complete **Markdown + HTML** outputs for optimal reading

---

## Overview

This system extracts text from PDFs, splits it into manageable chunks, and uses Claude Code for high-quality translation. Designed for translating large documents (200+ pages) without API costs.

## Features

- ✅ No API costs (uses Claude Code session)
- ✅ High-quality literary translation
- ✅ Progress tracking and resume capability
- ✅ Multiple output formats (Markdown, HTML)
- ✅ Interactive workflow with review points
- ✅ Reusable for any PDF in any language pair

## Project Structure

```
pdf-translator/
├── extract_pdf.py           # Extract and chunk PDF text
├── translate_helper.py      # Translation workflow helper
├── assemble_output.py       # Assemble final output
├── chunks/                  # Extracted source text
├── translations/            # Translated chunks
├── output/                  # Final combined output
└── progress.json            # Translation progress tracker
```

## Quick Start

### 1. Extract PDF into chunks

```bash
python3 extract_pdf.py "path/to/your.pdf" --chunk-size 20
```

This creates:
- Individual chunk files in `chunks/`
- Progress tracking in `progress.json`

### 2. Check translation status

```bash
python3 translate_helper.py --status
```

### 3. Translate chunks (Interactive)

```bash
# Show next untranslated chunk
python3 translate_helper.py --next

# Show specific chunk
python3 translate_helper.py --chunk 1
```

This displays the source text. Then in Claude Code, say:

```
"Translate chunk 1 to English and save it"
```

Claude Code will:
1. Read the chunk
2. Translate it with high literary quality
3. Save to `translations/chunk_001_translation.md`

Repeat for each chunk, or say:
```
"Translate the next 5 chunks"
```

### 4. Assemble final output

```bash
# Create both Markdown and HTML
python3 assemble_output.py

# Just Markdown
python3 assemble_output.py --format markdown

# Check status without assembling
python3 assemble_output.py --status
```

Output files go to `output/` directory.

## Current Project Status

**Book:** Нетворкинг для разведчиков (Networking for Spies)
**Authors:** Elena Vavilova & Andrey Bezrukov
**Language:** Russian → English
**Total Pages:** 274
**Total Chunks:** 14 (20 pages each, except last)

## Translation Workflow Examples

### Translate one chunk at a time

```
You: "Show me chunk 1"
Claude: [Displays Russian text for pages 1-20]

You: "Translate this to English and save as chunk_001_translation.md"
Claude: [Translates and saves]

You: "Show next chunk"
Claude: [Displays chunk 2]
```

### Batch translation

```
You: "Translate chunks 1 through 5"
Claude: [Translates all 5 chunks sequentially]
```

### Resume after break

```
You: "What's our translation progress?"
Claude: [Shows status - e.g., 8/14 chunks done]

You: "Continue translating from where we left off"
Claude: [Picks up at chunk 9]
```

## Translation Quality Guidelines

Claude Code will maintain:

- **Literary quality:** Preserving author's voice and style
- **Context awareness:** Remembering terms and concepts from earlier
- **Structure preservation:** Chapter headings, formatting, emphasis
- **Cultural adaptation:** Handling idioms and cultural references
- **Consistency:** Same terms translated the same way throughout

## Output Formats

### Markdown
Clean, readable format with:
- Preserved structure and headings
- Page number references
- Easy to edit or convert further

### HTML
Styled web version with:
- Beautiful typography (serif fonts)
- Dark/light mode support
- Print-friendly CSS
- Responsive design

## Scripts Reference

### extract_pdf.py

```bash
# Basic usage
python3 extract_pdf.py "input.pdf"

# Custom chunk size
python3 extract_pdf.py "input.pdf" --chunk-size 15

# Custom output directory
python3 extract_pdf.py "input.pdf" --output-dir ~/my-translation

# Start from specific page
python3 extract_pdf.py "input.pdf" --start-page 50
```

### translate_helper.py

```bash
# Show status
python3 translate_helper.py --status

# Show next untranslated chunk
python3 translate_helper.py --next

# Show specific chunk
python3 translate_helper.py --chunk 5
```

### assemble_output.py

```bash
# Create all formats
python3 assemble_output.py

# Markdown only
python3 assemble_output.py --format markdown

# HTML only (requires 'markdown' package)
python3 assemble_output.py --format html

# Just check status
python3 assemble_output.py --status
```

## Requirements

- Python 3.6+
- PyPDF2 (installed automatically)
- markdown (optional, for HTML output)

Install optional dependencies:
```bash
pip3 install markdown
```

## Tips

### For Best Translation Quality

1. **Review periodically:** Check translations every few chunks
2. **Provide context:** If Claude seems off, mention the book's theme/style
3. **Adjust as needed:** You can ask Claude to retranslate sections differently

### For Large Documents

1. **Work in sessions:** Translate 3-5 chunks per session
2. **Save progress:** The system automatically tracks what's done
3. **Resume anytime:** Just run `--next` to continue

### For Different Languages

The system works with any language pair:

```bash
# Extract any PDF
python3 extract_pdf.py "chinese-book.pdf"

# When translating, specify:
"Translate this chunk from Chinese to English"
```

## Troubleshooting

### Chunk file not found
```bash
# Re-run extraction
python3 extract_pdf.py "your.pdf"
```

### Translation seems inconsistent
```
"Let me provide context: This book is about intelligence networking
and maintains a professional but engaging tone."
```

### Want to retranslate a chunk
```
"Retranslate chunk 3 with a more formal tone"
```

## Use Cases

- 📚 Translating books
- 📄 Academic papers
- 📋 Technical documentation
- 📰 Long-form articles
- 🗂️ Any multi-page PDF with extractable text

## License

MIT License - Feel free to use and modify

## Credits

Created by Austin Morrissey with assistance from Claude (Anthropic)

Built specifically for translating "Networking for Spies" (Russian → English), but designed to be reusable for any translation project.
