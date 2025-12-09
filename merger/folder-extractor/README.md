# folder-extractor

Universal Folder to Text Converter

## Overview

`folder-extractor` converts any folder into AI-friendly text format by extracting content from multiple file types including PDFs, images, Office documents, and more. Best-effort approach for maximum content extraction.

## Features

- **Multi-format support**: Text, PDF, images, Office documents
- **OCR integration**: Optional OCR for images (Tesseract or iOS Shortcuts)
- **Configurable**: TOML-based configuration
- **Auto-splitting**: Split large outputs into manageable parts
- **Best-effort**: Continues on errors, reports what couldn't be extracted

## Installation

### Basic Installation (Text Files Only)

```bash
chmod +x folder_extractor.py
```

### Full Installation (with PDF, Image, Office Support)

```bash
# PDF support
pip install PyPDF2 pdfplumber

# OCR support (Tesseract)
pip install pytesseract Pillow
# Also install Tesseract OCR system package:
# - macOS: brew install tesseract
# - Ubuntu: apt-get install tesseract-ocr
# - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki

# Office support
pip install python-docx python-pptx openpyxl
```

### iOS/Pythonista

For iOS Shortcuts OCR integration, no additional packages needed. Configure via TOML (see Configuration below).

## Usage

### Basic Usage

```bash
# Extract current directory
./folder_extractor.py

# Extract specific folder
./folder_extractor.py --root /path/to/folder

# Custom output
./folder_extractor.py --root ~/Documents/scans --out scans_dump.md
```

### Options

```
--root, -r PATH          Source folder (default: current directory)
--out, -o PATH           Output file path (default: auto-generated)
--max-file-bytes BYTES   Max bytes to read per file (default: 10MB)
--max-output-bytes BYTES Max bytes per output file, enables splitting (default: 5MB)
--help, -h               Show this help message
```

### Examples

```bash
# Extract folder with all defaults
folder-extractor --root ~/Documents/project

# Large folder with controlled splitting
folder-extractor --root /data --max-output-bytes 10000000

# Single file, no splitting
folder-extractor --root ~/notes --max-output-bytes 0 --out notes.md
```

## Configuration

Create `~/.config/folder-extractor/config.toml` for advanced settings:

### OCR with Tesseract

```toml
[ocr]
backend = "tesseract"
```

### OCR with iOS Shortcuts

```toml
[ocr]
backend = "shortcut"
shortcut_name = "FolderExtractor OCR"
```

Create an iOS Shortcut that:
1. Receives a file path as input (text)
2. Loads the image
3. Extracts text with "Extract Text from Image" action
4. Returns the extracted text

### Disable OCR

```toml
[ocr]
backend = "none"
```

## Supported File Types

### Text Files
- **Method**: Direct read
- **Extensions**: `.txt`, `.md`, `.py`, `.js`, `.json`, `.yaml`, `.toml`, `.html`, `.css`, `.xml`, and many more
- **Required**: None (built-in)

### PDF Files
- **Method**: Text extraction
- **Extensions**: `.pdf`
- **Required**: `PyPDF2` or `pdfplumber`

### Images
- **Method**: OCR (Optical Character Recognition)
- **Extensions**: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.tif`, `.tiff`
- **Required**: `pytesseract` + Tesseract OCR, or iOS Shortcuts

### Office Documents
- **Method**: Library-based extraction
- **Word**: `.docx` (requires `python-docx`)
- **PowerPoint**: `.pptx` (requires `python-pptx`)
- **Excel**: `.xlsx` (requires `openpyxl`)

### Binary Files
- **Method**: Skipped
- **Extensions**: `.zip`, `.exe`, `.mp3`, `.mp4`, etc.
- **Note**: Listed in output but not processed

## Output Format

Each extraction creates a Markdown file with:

1. **Header**: Source folder, timestamp, file count
2. **File Sections**: One per file with:
   - Path, type, size, extraction method
   - Extracted content (if available)
   - Error messages (if extraction failed)
3. **Summary**: Statistics on file types and extraction methods

Example output:

```markdown
# Folder Extractor Report: myproject

- **Source:** `/home/user/myproject`
- **Generated:** 2025-12-09 10:30
- **Files:** 25

## File: README.md

- **Type:** text
- **Size:** 2.3 KB
- **Method:** text
- **MD5:** `abc123...`

```markdown
# My Project
...
```

## File: scan001.png

- **Type:** image
- **Size:** 456.7 KB
- **Method:** ocr_tesseract
- **MD5:** `def456...`

```text
Extracted text from image...
```

## File: document.pdf

- **Type:** pdf
- **Size:** 1.2 MB
- **Method:** pdf_pypdf2
- **MD5:** `ghi789...`

```text
PDF content...
```

---

## Summary

- **Total Files:** 25
- **Total Size:** 15.7 MB

**File Types:**
- text: 15
- image: 5
- pdf: 3
- binary: 2

**Extraction Methods:**
- text: 15
- ocr_tesseract: 5
- pdf_pypdf2: 3
- binary_skipped: 2
```

## Extraction Methods

The tool reports the method used for each file:

- `text`: Direct text read
- `text_truncated`: Text file was truncated (exceeded max-file-bytes)
- `pdf_pypdf2`: PDF extracted with PyPDF2
- `pdf_pdfplumber`: PDF extracted with pdfplumber
- `pdf_no_library`: PDF library not available
- `ocr_tesseract`: Image OCR with Tesseract
- `ocr_shortcut`: Image OCR with iOS Shortcuts
- `ocr_disabled`: OCR not configured
- `office_docx`: Word document extraction
- `office_pptx`: PowerPoint extraction
- `office_xlsx`: Excel extraction
- `office_*_not_installed`: Office library not available
- `binary_skipped`: Binary file skipped
- `error: ...`: Extraction error with details

## Ignored Items

The following are automatically skipped:

**Directories:**
- `.git`, `.hg`, `.svn`
- `__pycache__`, `.mypy_cache`
- `node_modules`, `dist`, `build`
- `.venv`, `venv`
- `.idea`, `.vscode`

**Files:**
- `.lock`, `.log` suffixes

## Comparison with Other Tools

### vs. repo-merger

`folder-extractor` is for **any content** (PDFs, images, Office).

`repo-merger` is for **code repositories** (text only).

Use `folder-extractor` for documents and mixed content, `repo-merger` for code projects.

### vs. all-ein-wandler

`folder-extractor` is the successor to `all-ein-wandler`, with:
- Clearer purpose and naming
- Better library support detection
- More robust error handling
- Improved output format

## Troubleshooting

### "PDF library not installed"

Install PDF support:
```bash
pip install PyPDF2 pdfplumber
```

### "OCR not working"

For Tesseract:
```bash
# Install system package
brew install tesseract  # macOS
apt-get install tesseract-ocr  # Ubuntu

# Install Python package
pip install pytesseract Pillow
```

For iOS Shortcuts: Create the shortcut as described in Configuration section.

### "Office library not installed"

```bash
pip install python-docx python-pptx openpyxl
```

### Output too large

Use `--max-output-bytes` to enable splitting:
```bash
folder-extractor --root . --max-output-bytes 5000000
```

## License

Part of the Heimgewebe tools collection.
