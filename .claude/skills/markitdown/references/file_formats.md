# File Format Support

This document provides detailed information about each file format supported by MarkItDown.

## Document Formats

### PDF (.pdf)

**Capabilities**:
- Text extraction
- Table detection
- Metadata extraction
- OCR for scanned documents (with dependencies)

**Dependencies**:
```bash
pip install 'markitdown[pdf]'
```

**Best For**:
- Scientific papers
- Reports
- Books
- Forms

**Limitations**:
- Complex layouts may not preserve perfect formatting
- Scanned PDFs require OCR setup
- Some PDF features (annotations, forms) may not convert

**Example**:
```python
from markitdown import MarkItDown

md = MarkItDown()
result = md.convert("research_paper.pdf")
print(result.text_content)
```

---

### Microsoft Word (.docx)

**Capabilities**:
- Text extraction
- Table conversion
- Heading hierarchy
- List formatting
- Basic text formatting (bold, italic)

**Dependencies**:
```bash
pip install 'markitdown[docx]'
```

**Best For**:
- Research papers
- Reports
- Documentation
- Manuscripts

**Preserved Elements**:
- Headings (converted to Markdown headers)
- Tables (converted to Markdown tables)
- Lists (bulleted and numbered)
- Basic formatting (bold, italic)
- Paragraphs

**Example**:
```python
result = md.convert("manuscript.docx")
```

---

### PowerPoint (.pptx)

**Capabilities**:
- Slide content extraction
- Speaker notes
- Table extraction
- Image descriptions (with AI)

**Dependencies**:
```bash
pip install 'markitdown[pptx]'
```

**Best For**:
- Presentations
- Lecture slides
- Conference talks

**Output Format**:
```markdown
# Slide 1: Title

Content from slide 1...

**Notes**: Speaker notes appear here

---

# Slide 2: Next Topic

...
```

---

### Excel (.xlsx, .xls)

**Capabilities**:
- Sheet extraction
- Table formatting
- Data preservation
- Formula values (calculated)

**Dependencies**:
```bash
pip install 'markitdown[xlsx]'  # Modern Excel
pip install 'markitdown[xls]'   # Legacy Excel
```

**Best For**:
- Data tables
- Research data
- Statistical results
- Experimental data

**Output Format**:
```markdown
# Sheet: Results

| Sample | Control | Treatment | P-value |
|--------|---------|-----------|---------|
| 1      | 10.2    | 12.5      | 0.023   |
| 2      | 9.8     | 11.9      | 0.031   |
```

**Example**:
```python
result = md.convert("experimental_data.xlsx")
```

---

## Image Formats

### Images (.jpg, .jpeg, .png, .gif, .webp)

**Capabilities**:
- EXIF metadata extraction
- OCR text extraction
- AI-powered image descriptions

**Dependencies**:
```bash
pip install 'markitdown[all]'  # Includes image support
```

**Best For**:
- Scanned documents
- Charts and graphs
- Scientific diagrams
- Photographs with text

**Output Without AI**:
```markdown
![Image](image.jpg)

**EXIF Data**:
- Camera: Canon EOS 5D
- Date: 2024-01-15
- Resolution: 4000x3000
```

**OCR for Text Extraction**:
Requires Tesseract OCR:
```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr
```

---

## Audio Formats

### Audio (.wav, .mp3)

**Not permitted in this setup.** MarkItDown's audio transcription sends the
audio to an external speech service (Google Web Speech API). Do not install
`[audio-transcription]` and do not convert audio files.

---

## Web Formats

### HTML (.html, .htm)

**Capabilities**:
- Clean HTML to Markdown conversion
- Link preservation
- Table conversion
- List formatting

**Best For**:
- Web pages
- Documentation
- Blog posts
- Online articles

**Output Format**: Clean Markdown with preserved links and structure

**Example**:
```python
result = md.convert("webpage.html")
```

---

## Data Formats

### CSV (.csv)

**Capabilities**:
- Automatic table conversion
- Delimiter detection
- Header preservation

**Output Format**: Markdown tables

**Example**:
```python
result = md.convert("data.csv")
```

**Output**:
```markdown
| Column1 | Column2 | Column3 |
|---------|---------|---------|
| Value1  | Value2  | Value3  |
```

---

### JSON (.json)

**Capabilities**:
- Structured representation
- Pretty formatting
- Nested data visualization

**Best For**:
- API responses
- Configuration files
- Data exports

**Example**:
```python
result = md.convert("data.json")
```

---

### XML (.xml)

**Capabilities**:
- Structure preservation
- Attribute extraction
- Formatted output

**Best For**:
- Configuration files
- Data interchange
- Structured documents

**Example**:
```python
result = md.convert("config.xml")
```

---

## Archive Formats

### ZIP (.zip)

**Capabilities**:
- Iterates through archive contents
- Converts each file individually
- Maintains directory structure in output

**Best For**:
- Document collections
- Project archives
- Batch conversions

**Output Format**:
```markdown
# Archive: documents.zip

## File: document1.pdf
[Content from document1.pdf...]

---

## File: document2.docx
[Content from document2.docx...]
```

**Example**:
```python
result = md.convert("archive.zip")
```

---

## E-book Formats

### EPUB (.epub)

**Capabilities**:
- Full text extraction
- Chapter structure
- Metadata extraction

**Best For**:
- E-books
- Digital publications
- Long-form content

**Output Format**: Markdown with preserved chapter structure

**Example**:
```python
result = md.convert("book.epub")
```

---

## Other Formats

### Outlook Messages (.msg)

**Capabilities**:
- Email content extraction
- Attachment listing
- Metadata (from, to, subject, date)

**Dependencies**:
```bash
pip install 'markitdown[outlook]'
```

**Best For**:
- Email archives
- Communication records

**Example**:
```python
result = md.convert("message.msg")
```

---

## Format-Specific Tips

### PDF Best Practices

1. **For scanned PDFs, ensure OCR is set up**:
   ```bash
   brew install tesseract  # macOS
   ```

2. **Split very large PDFs before conversion** for better performance

### PowerPoint Best Practices

1. **Check speaker notes** - they're included in output

2. **Complex animations won't be captured** - static content only

### Excel Best Practices

1. **Large spreadsheets** may take time to convert

2. **Formulas are converted to their calculated values**

3. **Multiple sheets** are all included in output

4. **Charts become text descriptions**

### Image Best Practices

1. **For text-heavy images, ensure OCR dependencies** are installed

2. **High-resolution images** may take longer to process

## Unsupported Formats

If you need to convert an unsupported format:

1. **Create a custom converter** (see `api_reference.md`)
2. **Look for plugins** on GitHub (#markitdown-plugin)
3. **Pre-convert to supported format** (e.g., convert .rtf to .docx)

---

## Format Detection

MarkItDown automatically detects format from:

1. **File extension** (primary method)
2. **MIME type** (fallback)
3. **File signature** (magic bytes, fallback)

**Override detection**:
```python
# Force specific format
result = md.convert("file_without_extension", file_extension=".pdf")

# With streams
with open("file", "rb") as f:
    result = md.convert_stream(f, file_extension=".pdf")
```

