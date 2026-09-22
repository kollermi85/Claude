#!/usr/bin/env python3
"""
Convert attached files to Markdown - strictly locally.

Usage:
    python convert.py [FILE_OR_DIR ...] [--out OUT_DIR]

Without arguments, all files in /mnt/user-data/uploads are converted.
Output: one <name>.md per input file in OUT_DIR
(default: /mnt/user-data/outputs/markdown if that exists, else ./markdown).

Order of attempts per file:
  1. Microsoft MarkItDown (installed on demand, incl. cryptography/cffi repair)
  2. Built-in fallback converters (pdfplumber/pypdf, openpyxl, python-pptx,
     stdlib for DOCX/CSV/JSON/HTML/TXT)

Privacy: no document content is ever sent anywhere. MarkItDown is used without
LLM client, without Azure Document Intelligence and without plugins; audio,
video and URLs are refused. The only network access is `pip install` from PyPI
when MarkItDown is missing.
"""

import argparse
import csv
import html
import io
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

DEFAULT_IN = Path("/mnt/user-data/uploads")
DEFAULT_OUT = Path("/mnt/user-data/outputs/markdown")

# Formats whose conversion would require an external service -> refused.
REFUSED = {".mp3", ".wav", ".m4a", ".ogg", ".flac", ".mp4", ".mov", ".avi", ".mkv", ".webm"}
# Already text: copied/wrapped, no conversion needed.
PLAIN = {".md", ".markdown", ".txt", ".log"}

PIP_EXTRAS = "markitdown[pdf,docx,pptx,xlsx,xls,outlook]"


# --------------------------------------------------------------------------
# MarkItDown bootstrap
# --------------------------------------------------------------------------

def _pip(*args):
    base = [sys.executable, "-m", "pip", "install", "-q", "--disable-pip-version-check"]
    for extra in ([], ["--break-system-packages"]):
        r = subprocess.run(base + extra + list(args), capture_output=True, text=True)
        if r.returncode == 0:
            return True
    return False


def _try_import():
    """Import MarkItDown in a subprocess first: a broken cryptography build can
    crash the interpreter (pyo3 panic) instead of raising a normal exception."""
    probe = subprocess.run(
        [sys.executable, "-c", "from markitdown import MarkItDown; MarkItDown()"],
        capture_output=True, text=True,
    )
    return probe.returncode == 0, probe.stderr


def load_markitdown(allow_install=True):
    ok, err = _try_import()
    if not ok and allow_install:
        if "No module named 'markitdown'" in err or "No module named 'markitdown." in err:
            _pip(PIP_EXTRAS)
            ok, err = _try_import()
        if not ok and ("cffi" in err or "cryptography" in err or "pyo3" in err or "PanicException" in err):
            # Known issue: system cryptography does not match the pip-installed cffi.
            _pip("--ignore-installed", "cffi", "cryptography")
            ok, err = _try_import()
        if not ok and "No module named" in err:
            _pip(PIP_EXTRAS)
            ok, err = _try_import()
    if not ok:
        return None
    from markitdown import MarkItDown
    # Plain constructor: no llm_client, no docintel_endpoint, no plugins.
    return MarkItDown(enable_plugins=False)


# --------------------------------------------------------------------------
# Fallback converters (local libraries / stdlib only)
# --------------------------------------------------------------------------

def _md_table(rows):
    rows = [["" if c is None else str(c).replace("|", "\\|").replace("\n", " ") for c in r] for r in rows]
    rows = [r for r in rows if any(c.strip() for c in r)]
    if not rows:
        return ""
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return "\n".join(out)


def fb_pdf(p):
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(p) as pdf:
            for i, page in enumerate(pdf.pages, 1):
                parts.append(f"## Seite {i}\n\n{page.extract_text() or ''}")
                for t in page.extract_tables() or []:
                    parts.append(_md_table(t))
        return "\n\n".join(parts)
    except ImportError:
        from pypdf import PdfReader
        return "\n\n".join(f"## Seite {i}\n\n{pg.extract_text() or ''}"
                           for i, pg in enumerate(PdfReader(str(p)).pages, 1))


def fb_docx(p):
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    import xml.etree.ElementTree as ET
    root = ET.fromstring(zipfile.ZipFile(p).read("word/document.xml"))
    body = root.find("w:body", ns)
    out = []
    for el in body:
        tag = el.tag.split("}")[1]
        if tag == "p":
            text = "".join(t.text or "" for t in el.iter(f"{{{ns['w']}}}t"))
            style = el.find("w:pPr/w:pStyle", ns)
            s = style.get(f"{{{ns['w']}}}val", "") if style is not None else ""
            m = re.search(r"(\d)$", s) if s.lower().startswith(("heading", "berschrift", "überschrift")) else None
            if text.strip():
                out.append(("#" * int(m.group(1)) + " " if m else "") + text)
        elif tag == "tbl":
            rows = [["".join(t.text or "" for t in c.iter(f"{{{ns['w']}}}t")) for c in r.findall("w:tc", ns)]
                    for r in el.findall("w:tr", ns)]
            out.append(_md_table(rows))
    return "\n\n".join(out)


def fb_xlsx(p):
    import openpyxl
    wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
    return "\n\n".join(f"## {ws.title}\n\n{_md_table(list(ws.iter_rows(values_only=True)))}" for ws in wb.worksheets)


def fb_pptx(p):
    from pptx import Presentation
    out = []
    for i, slide in enumerate(Presentation(p).slides, 1):
        out.append(f"## Folie {i}")
        for sh in slide.shapes:
            if sh.has_text_frame and sh.text_frame.text.strip():
                out.append(sh.text_frame.text)
            if getattr(sh, "has_table", False) and sh.has_table:
                out.append(_md_table([[c.text for c in r.cells] for r in sh.table.rows]))
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            out.append("**Notizen:** " + slide.notes_slide.notes_text_frame.text)
    return "\n\n".join(out)


def fb_csv(p):
    raw = p.read_text(encoding="utf-8-sig", errors="replace")
    try:
        dialect = csv.Sniffer().sniff(raw[:4096], delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    return _md_table(list(csv.reader(io.StringIO(raw), dialect)))


def fb_json(p):
    return "```json\n" + json.dumps(json.loads(p.read_text(encoding="utf-8")), indent=2, ensure_ascii=False) + "\n```"


def fb_html(p):
    raw = p.read_text(encoding="utf-8", errors="replace")
    try:
        from bs4 import BeautifulSoup
        return BeautifulSoup(raw, "html.parser").get_text("\n", strip=True)
    except ImportError:
        return html.unescape(re.sub(r"<[^>]+>", " ", raw))


def pdf_tables(p):
    """Tables detected by pdfplumber, appended to MarkItDown's PDF text
    (pdfminer loses table structure - critical for area and cost tables)."""
    try:
        import pdfplumber
    except ImportError:
        return ""
    parts = []
    with pdfplumber.open(p) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            for t in page.extract_tables() or []:
                table = _md_table(t)
                if table:
                    parts.append(f"**Tabelle (Seite {i})**\n\n{table}")
    return ("\n\n## Erkannte Tabellen\n\n" + "\n\n".join(parts)) if parts else ""


# Formats where the own converter is better than MarkItDown
# (MarkItDown assumes comma-separated CSV; Austrian/German Excel exports use ";").
PREFER_OWN = {".csv", ".tsv"}

FALLBACKS = {
    ".pdf": fb_pdf, ".docx": fb_docx, ".xlsx": fb_xlsx, ".xlsm": fb_xlsx, ".pptx": fb_pptx,
    ".csv": fb_csv, ".tsv": fb_csv, ".json": fb_json, ".html": fb_html, ".htm": fb_html,
}


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def target_path(out_dir, p):
    # "<name>.<ext>.md" keeps plan.pdf and plan.docx apart; reruns overwrite.
    return out_dir / f"{p.name}.md"


def convert_one(p, md, out_dir):
    ext = p.suffix.lower()
    if ext in REFUSED:
        return None, "abgelehnt", "Audio/Video wird nicht umgewandelt (würde einen externen Dienst erfordern)", 0
    text, method, note = None, None, ""
    if ext in PLAIN:
        text, method = p.read_text(encoding="utf-8", errors="replace"), "Text"
    if text is None and ext in PREFER_OWN:
        try:
            text, method = FALLBACKS[ext](p), "eigener Konverter"
        except Exception as e:
            note = f"CSV: {type(e).__name__}"
    if text is None and md is not None:
        try:
            text, method = md.convert(str(p)).text_content, "MarkItDown"
            if ext == ".pdf":
                try:
                    text += pdf_tables(p)
                except Exception:
                    pass
        except Exception as e:  # unsupported or corrupt -> try fallback
            note = f"MarkItDown: {type(e).__name__}"
    if (text is None or not text.strip()) and ext in FALLBACKS:
        try:
            text, method = FALLBACKS[ext](p), "Fallback"
        except Exception as e:
            note = (note + "; " if note else "") + f"Fallback: {type(e).__name__}: {e}"
    if text is None:
        return None, "fehlgeschlagen", note or "Format nicht unterstützt", 0
    text = re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"
    if ext == ".pdf" and len(text.strip()) < 50:
        note = (note + "; " if note else "") + "kaum Text gefunden - vermutlich gescanntes PDF (OCR nötig)"
    target = target_path(out_dir, p)
    target.write_text(f"<!-- Quelle: {p.name} -->\n\n" + text, encoding="utf-8")
    return target, method, note, len(text)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="*", type=Path)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--no-install", action="store_true", help="MarkItDown nicht nachinstallieren")
    ap.add_argument("--fallback-only", action="store_true", help="Nur eingebaute Konverter nutzen")
    args = ap.parse_args()

    inputs = args.inputs or [DEFAULT_IN]
    files = []
    for i in inputs:
        if i.is_dir():
            files += sorted(f for f in i.rglob("*") if f.is_file() and not f.name.startswith("."))
        elif i.is_file():
            files.append(i)
        else:
            print(f"Nicht gefunden: {i}", file=sys.stderr)
    if not files:
        print("Keine Dateien zum Umwandeln gefunden.")
        return 1

    out_dir = args.out or (DEFAULT_OUT if DEFAULT_OUT.parent.exists() else Path("markdown"))
    out_dir.mkdir(parents=True, exist_ok=True)

    md = None if args.fallback_only else load_markitdown(allow_install=not args.no_install)
    print(f"Konverter: {'MarkItDown' if md else 'eingebaute Fallbacks'} | Ausgabe: {out_dir}\n")

    failed = 0
    for f in files:
        target, method, note, size = convert_one(f, md, out_dir)
        if target:
            print(f"OK   {f.name} -> {target.name}  [{method}, {size:,} Zeichen, ~{size // 4:,} Tokens]"
                  + (f"  HINWEIS: {note}" if note else ""))
        else:
            failed += 1
            print(f"FEHL {f.name}  [{method}] {note}")
    return 1 if failed == len(files) else 0


if __name__ == "__main__":
    sys.exit(main())
