#!/usr/bin/env python3
"""Konvertiert Dateien (PDF, DOCX, PPTX, XLSX, HTML, TXT, ...) nach Markdown.

Nutzung (lokal oder in Replit-Terminal):
    python convert_to_md.py datei1.pdf datei2.docx ...
    python convert_to_md.py --input-dir uploads --output-dir output

In Replit: Dateien per Upload-UI in den Projektordner (z.B. "uploads/")
legen, dann im Shell/Run-Terminal obigen Befehl ausführen. Die erzeugten
.md-Dateien landen im "output/"-Ordner und können danach heruntergeladen
werden.
"""

import argparse
import sys
from pathlib import Path

from markitdown import MarkItDown

SUPPORTED_SUFFIXES = {
    ".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".html", ".htm",
    ".txt", ".csv", ".json", ".xml", ".epub",
}


def convert_file(md: MarkItDown, src: Path, output_dir: Path) -> Path:
    result = md.convert(str(src))
    output_dir.mkdir(parents=True, exist_ok=True)
    dest = output_dir / (src.stem + ".md")
    dest.write_text(result.text_content, encoding="utf-8")
    return dest


def collect_inputs(files: list[str], input_dir: str | None) -> list[Path]:
    paths: list[Path] = [Path(f) for f in files]
    if input_dir:
        base = Path(input_dir)
        paths.extend(p for p in base.iterdir() if p.suffix.lower() in SUPPORTED_SUFFIXES)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="*", help="Zu konvertierende Dateien")
    parser.add_argument("--input-dir", default=None, help="Ordner mit Dateien, die konvertiert werden sollen")
    parser.add_argument("--output-dir", default="output", help="Zielordner für die .md-Dateien (Standard: output)")
    args = parser.parse_args()

    inputs = collect_inputs(args.files, args.input_dir)
    if not inputs:
        parser.error("Keine Eingabedateien angegeben. Nutze Dateipfade oder --input-dir.")

    md = MarkItDown()
    output_dir = Path(args.output_dir)

    exit_code = 0
    for src in inputs:
        if not src.exists():
            print(f"FEHLER: Datei nicht gefunden: {src}", file=sys.stderr)
            exit_code = 1
            continue
        try:
            dest = convert_file(md, src, output_dir)
            print(f"OK: {src} -> {dest}")
        except Exception as exc:
            print(f"FEHLER bei {src}: {exc}", file=sys.stderr)
            exit_code = 1

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
