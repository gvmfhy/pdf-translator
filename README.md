# PDF Translator

A chunked workflow for extracting, reviewing, and assembling long-form PDF
translations. The repository also contains a fully reviewed Russian-to-English
translation of *Networking for Spies* by Elena Vavilova and Andrey Bezrukov.

## Reviewed Book Project

The original translation was completed in 14 chunks and then checked line by
line against the complete 274-page Russian source edition. The review covered:

- all 14 translation chunks and all 13 chunk boundaries;
- every source page, including image-only pages;
- all 86 table-of-contents entries and their body headings;
- names, dates, numbers, acronyms, lists, and intelligence terminology;
- the original edition's 34 visual elements, including translated recreations
  of diagrams and tables.

The corrected chunk files in `translations/` are the canonical reviewed text.
The combined Markdown and HTML files in `output/` are generated from them.

The polished PDF builder is included, but the compiled book PDF and extracted
illustrations are not committed. Readers must provide their own legally
obtained copy of the same source edition. See [NOTICE.md](NOTICE.md).

## Repository Layout

~~~text
pdf-translator/
├── chunks/                         # Extracted source text, 20 pages per chunk
├── translations/                   # Canonical reviewed English chunks
├── output/                         # Generated Markdown and HTML
├── docs/networking_for_spies_review_guide.md
├── scripts/
│   ├── build_networking_for_spies_pdf.py
│   ├── extract_pdf_images.py
│   └── verify_networking_for_spies.py
├── extract_pdf.py                  # Generic PDF text extraction/chunking
├── translate_helper.py             # Chunk workflow helper
├── assemble_output.py              # Markdown and HTML assembler
├── progress.json                   # Translation project metadata
└── requirements.txt
~~~

## Set Up

Python 3.9 or newer is recommended.

~~~bash
git clone https://github.com/gvmfhy/pdf-translator.git
cd pdf-translator
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
~~~

On Windows PowerShell, activate the environment with:

~~~powershell
.venv\Scripts\Activate.ps1
~~~

## Generate the Reviewed Text Outputs

From the repository root:

~~~bash
python assemble_output.py
~~~

This regenerates the combined Markdown and HTML files in `output/` from the 14
reviewed translation chunks.

## Build the Reviewed PDF Locally

The PDF edition uses the original illustrations and translated recreations of
the source diagrams. Install Poppler first so `pdfimages` and `pdfinfo` are
available:

~~~bash
# macOS
brew install poppler

# Debian/Ubuntu
sudo apt-get install poppler-utils
~~~

Then use your own copy of the source PDF:

~~~bash
python scripts/extract_pdf_images.py "/path/to/Networking for Spies.pdf"

python scripts/build_networking_for_spies_pdf.py \
  --translations-dir translations \
  --image-dir assets/source_images \
  --output output/Networking_for_Spies_Reviewed_English_Translation.pdf
~~~

The builder automatically finds Arial/Times New Roman, DejaVu, or Liberation
fonts on common macOS, Linux, and Windows installations. On an unusual setup,
pass `--font-dir /path/to/fonts`.

Run the structural verifier against the same source edition:

~~~bash
python scripts/verify_networking_for_spies.py \
  --project-dir . \
  --source-pdf "/path/to/Networking for Spies.pdf" \
  --pdf output/Networking_for_Spies_Reviewed_English_Translation.pdf
~~~

The verifier checks source-page coverage, source extraction integrity,
translation residue patterns, required book sections, PDF metadata, and
forbidden chunk-processing artifacts. It prints a JSON report and exits with a
nonzero status if any strict book-level check fails.

## Use the Generic Translation Workflow

To start a separate PDF translation project in another directory:

~~~bash
python extract_pdf.py "/path/to/input.pdf" --output-dir "/path/to/project"
python translate_helper.py --project-dir "/path/to/project" --status
python translate_helper.py --project-dir "/path/to/project" --next
python assemble_output.py --project-dir "/path/to/project"
~~~

The extractor defaults to 20 pages per chunk. Override that with
`--chunk-size`, or start at a later page with `--start-page`.

For reliable long-document translation, review each chunk against its source,
maintain a shared terminology guide, and audit every boundary after assembly.
The method used for this book is in
[docs/networking_for_spies_review_guide.md](docs/networking_for_spies_review_guide.md).

## Software Licence and Book Rights

The software code and original project documentation are available under the
MIT licence in [LICENSE](LICENSE). That licence does not apply to the source
book, translated book text, cover art, illustrations, or other source-derived
material. Those remain subject to the rights described in [NOTICE.md](NOTICE.md).

## Credits

Created by Austin Morrissey with AI-assisted translation and review workflows.
The reviewed English edition was audited and assembled with Codex.
