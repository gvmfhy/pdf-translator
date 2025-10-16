# Quick Start Guide - PDF Translation

## Current Status

✅ **System is ready!**
- PDF extracted: 274 pages → 14 chunks
- Progress tracking: Active
- Ready to translate: Chunk 1

## How to Translate (Simple 3-Step Process)

### Step 1: View Next Chunk
```bash
python3 translate_helper.py --next
```

This shows you the Russian text to translate.

### Step 2: Ask Claude Code to Translate

In this Claude Code session, simply say:

```
"Translate chunk 1 to English and save it"
```

Or for multiple chunks:

```
"Translate the next 3 chunks"
```

### Step 3: Check Progress

```bash
python3 translate_helper.py --status
```

## When Translation is Complete

Assemble the final book:

```bash
python3 assemble_output.py
```

This creates:
- `output/[book_name]_english.md` - Markdown version
- `output/[book_name]_english.html` - Styled web version

## Example Translation Session

```
You: "Show translation status"
Claude: [Shows 0/14 chunks done]

You: "Translate chunk 1"
Claude: [Reads chunk, translates, saves to translations/]

You: "Continue with chunk 2"
Claude: [Translates and saves]

You: "What's our progress now?"
Claude: [Shows 2/14 chunks done]

You: "Let's do 3 more chunks"
Claude: [Translates chunks 3, 4, 5]

[Take a break - progress is saved]

You: "Resume translation"
Claude: [Starts from chunk 6]
```

## File Locations

```
~/pdf-translator/
├── chunks/                      ← Russian source text (read-only)
├── translations/                ← English translations (output)
├── output/                      ← Final assembled book
└── progress.json               ← Tracking file
```

## Quick Commands Reference

| Action | Command |
|--------|---------|
| Check status | `python3 translate_helper.py --status` |
| Show next chunk | `python3 translate_helper.py --next` |
| Show specific chunk | `python3 translate_helper.py --chunk 5` |
| Assemble final output | `python3 assemble_output.py` |
| Check what's assembled | `python3 assemble_output.py --status` |

## Ready to Start?

Try:
```
"Show me chunk 1 to translate"
```

Then:
```
"Translate this chunk to English and save it"
```

That's it! The system handles the rest.
