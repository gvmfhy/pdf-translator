# Quick Start

## Rebuild the Reviewed Markdown and HTML

~~~bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python assemble_output.py
~~~

The 14 files in `translations/` are the canonical reviewed English text.

## Build the Reviewed PDF

Install Poppler (`brew install poppler` on macOS or
`sudo apt-get install poppler-utils` on Debian/Ubuntu), then run:

~~~bash
python scripts/extract_pdf_images.py "/path/to/Networking for Spies.pdf"

python scripts/build_networking_for_spies_pdf.py \
  --translations-dir translations \
  --image-dir assets/source_images \
  --output output/Networking_for_Spies_Reviewed_English_Translation.pdf

python scripts/verify_networking_for_spies.py \
  --project-dir . \
  --source-pdf "/path/to/Networking for Spies.pdf" \
  --pdf output/Networking_for_Spies_Reviewed_English_Translation.pdf
~~~

The compiled PDF and extracted source illustrations are intentionally ignored
by Git. Supply your own legally obtained copy of the same source edition. See
`NOTICE.md` for the distinction between the software licence and book rights.

## Start a Different Translation Project

~~~bash
python extract_pdf.py "/path/to/input.pdf" --output-dir "/path/to/project"
python translate_helper.py --project-dir "/path/to/project" --next
python assemble_output.py --project-dir "/path/to/project"
~~~

See `README.md` for the complete workflow and
`docs/networking_for_spies_review_guide.md` for the review methodology used
on this book.
