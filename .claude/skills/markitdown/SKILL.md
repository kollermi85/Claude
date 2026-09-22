---
name: markitdown
description: "Convert files and office documents to Markdown, fully offline. Supports PDF, DOCX, PPTX, XLSX, images (EXIF + local OCR), HTML, CSV, JSON, XML, ZIP, EPUB and Outlook MSG."
allowed-tools: [Read, Write, Edit, Bash]
license: MIT
source: https://github.com/microsoft/markitdown
---

# MarkItDown - File to Markdown Conversion (local only)

## Overview

MarkItDown is a Python tool developed by Microsoft for converting various file
formats to Markdown. Markdown is token-efficient and well understood by
language models, so converted documents are easy to read, search and summarize.

## Privacy rule: no data leaves the machine

This skill is configured for **strictly local processing**. Document content
must never be sent to an external service. Therefore:

- **Never** pass `llm_client`, `llm_model` or `llm_prompt` to `MarkItDown()`
  (these send images/slides to a remote AI API).
- **Never** pass `docintel_endpoint` (Azure Document Intelligence is a cloud service).
- **Never** convert audio files and never install `[audio-transcription]`
  (transcription uses the Google Web Speech API).
- **Never** convert YouTube or other URLs, and never install `[youtube-transcription]`.
- **Never** install or enable third-party plugins (`enable_plugins=True`,
  `--use-plugins`) - their behavior is not reviewed.
- Always use plain `MarkItDown()` (or `MarkItDown(enable_plugins=False)`).

If a request would require any of the above, explain why it is not done and
offer a local alternative instead.

## Supported Formats

| Format | Description | Notes |
|--------|-------------|-------|
| **PDF** | Portable Document Format | Full text extraction |
| **DOCX** | Microsoft Word | Tables, formatting preserved |
| **PPTX** | PowerPoint | Slides with notes |
| **XLSX / XLS** | Excel spreadsheets | Tables and data |
| **Images** | JPEG, PNG, GIF, WebP | EXIF metadata + local OCR |
| **HTML** | Local HTML files | Clean conversion |
| **CSV** | Comma-separated values | Table format |
| **JSON** | JSON data | Structured representation |
| **XML** | XML documents | Structured format |
| **ZIP** | Archive files | Iterates contents |
| **EPUB** | E-books | Full text extraction |
| **MSG** | Outlook messages | Mail body and headers |

## Quick Start

### Installation

```bash
pip install 'markitdown[pdf,docx,pptx,xlsx,xls,outlook]'
```

### Command-Line Usage

```bash
# Basic conversion
markitdown path-to-file.pdf > document.md

# Specify output file
markitdown path-to-file.pdf -o document.md
```

### Python API

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("document.pdf")
print(result.text_content)

# Convert from stream
with open("document.pdf", "rb") as f:
    result = md.convert_stream(f, file_extension=".pdf")
```

## Common Use Cases

### 1. Convert a report or expert opinion (PDF)

```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("gutachten.pdf")
with open("gutachten.md", "w", encoding="utf-8") as f:
    f.write(result.text_content)
```

### 2. Extract data from Excel

```python
result = MarkItDown().convert("kostenaufstellung.xlsx")
# Each sheet becomes a Markdown table
print(result.text_content)
```

### 3. Process multiple documents

Use the bundled script (local only):

```bash
python scripts/batch_convert.py input_dir/ output_dir/
python scripts/convert_literature.py papers/ output/   # PDFs with metadata
```

## Best Practices

- **Scanned documents**: install `tesseract-ocr` locally for OCR.
- **Large files**: use `convert_stream()` and write the result directly to disk.
- **Token efficiency**: collapse blank lines, e.g.
  `re.sub(r'\n{3,}', '\n\n', result.text_content)`.
- **Errors**: wrap `md.convert()` in `try/except` and report the file that failed.

## Troubleshooting

1. **Missing dependencies**: `pip install 'markitdown[pdf]'` (or the relevant format).
2. **Binary file errors**: open files in binary mode (`"rb"`) for `convert_stream()`.
3. **OCR not working**: `sudo apt-get install tesseract-ocr` (Linux) or
   `brew install tesseract` (macOS).

## Resources

- **MarkItDown GitHub**: https://github.com/microsoft/markitdown
- **API reference**: `references/api_reference.md`
- **Format details**: `references/file_formats.md`
- **Examples**: `assets/example_usage.md`
