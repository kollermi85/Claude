---
name: datei-zu-markdown
description: Wandelt jede angehängte oder hochgeladene Datei (PDF, Word/DOCX, PowerPoint/PPTX, Excel/XLSX/XLS, CSV, HTML, JSON, EPUB, Outlook-MSG, ZIP) zuerst lokal mit Microsoft MarkItDown in Markdown um, bevor damit gearbeitet wird - ohne Cloud-Dienste, es verlassen keine Inhalte die Umgebung. IMMER verwenden, sobald der Nutzer eine Datei anhängt oder hochlädt, egal ob er zusammenfassen, prüfen, vergleichen, Zahlen herausziehen, Fragen dazu beantworten oder nur "schau dir das an" möchte - auch wenn er Markdown nicht erwähnt. Ebenso bei ausdrücklichen Anfragen wie "in Markdown umwandeln", "als .md", "Text aus der PDF holen".
---

# Datei zu Markdown (lokal)

Angehängte Dateien werden zuerst in Markdown umgewandelt und danach wird mit
dem Markdown gearbeitet. Markdown ist kompakt, gut durchsuchbar und behält
Überschriften und Tabellen bei - so lassen sich auch lange Gutachten,
Baubeschreibungen, Leistungsverzeichnisse oder Kostenaufstellungen vollständig
und ohne Textverlust auswerten.

## Datenschutz - warum alles lokal bleibt

Der Nutzer möchte ausdrücklich, dass keine Dokumentinhalte an externe Dienste
gehen. Deshalb:

- MarkItDown nur ohne `llm_client`, ohne `docintel_endpoint` (Azure) und ohne
  Plugins verwenden - genau so, wie es `scripts/convert.py` tut.
- Audio- und Videodateien nicht umwandeln (die Transkription liefe über einen
  Google-Dienst) und keine URLs/YouTube-Links abrufen.
- Keine Online-Konverter, OCR-APIs oder sonstigen Webdienste für Dateiinhalte.
- Einzige erlaubte Netzwerkverbindung: `pip install` von PyPI, falls MarkItDown fehlt.

Wenn eine Anfrage nur mit einem externen Dienst lösbar wäre, das kurz erklären
und eine lokale Alternative anbieten.

## Ablauf

1. **Umwandeln** - alle angehängten Dateien in einem Aufruf:

   ```bash
   python <skill-pfad>/scripts/convert.py
   ```

   Ohne Argumente nimmt das Skript alle Dateien aus `/mnt/user-data/uploads`
   und schreibt je eine `.md` nach `/mnt/user-data/outputs/markdown/`
   (sonst `./markdown/`). Einzelne Dateien oder Ordner können als Argumente
   übergeben werden, das Ziel mit `--out`.

   Das Skript kümmert sich selbst um die Einrichtung: Fehlt MarkItDown, wird es
   installiert; stürzt es wegen einer unpassenden `cryptography`/`cffi`-Version
   ab, werden diese Pakete repariert. Klappt beides nicht (z. B. kein
   Internetzugang), nutzt es eingebaute Ersatz-Konverter. Diese Schritte also
   nicht von Hand wiederholen - einfach das Skript laufen lassen und seine
   Ausgabe lesen.

2. **Ergebnis prüfen** - die Konsolenausgabe zeigt pro Datei Konverter,
   Umfang und Hinweise. Auf `HINWEIS` achten:
   - *vermutlich gescanntes PDF*: Es gibt keinen Textlayer. Dem Nutzer sagen,
     dass eine Texterkennung (OCR) nötig ist; lokal nur, wenn `tesseract`
     installiert ist.
   - *Fallback*: Umwandlung hat funktioniert, aber mit einfacherer Formatierung.

   Zwei Eigenheiten, die man kennen sollte:
   - **PDF-Tabellen**: Im Fließtext stehen Tabellenwerte oft zerstückelt
     untereinander. Das Skript hängt deshalb am Ende einen Abschnitt
     `## Erkannte Tabellen` an - für Flächen, Kosten und Termine immer diesen
     Abschnitt als Quelle nehmen.
   - **Excel-Formeln**: Es werden die zuletzt gespeicherten Ergebnisse gelesen.
     Steht bei Formelzellen `NaN` oder nichts, wurde die Datei nie in Excel
     berechnet gespeichert; das dem Nutzer sagen, statt Werte zu erfinden, und
     bei Bedarf selbst nachrechnen (mit Hinweis, dass nachgerechnet wurde).

3. **Mit dem Markdown arbeiten** - die erzeugte `.md` lesen statt der
   Originaldatei und damit die eigentliche Aufgabe erledigen (zusammenfassen,
   prüfen, vergleichen, Zahlen herausziehen ...). Bei sehr langen Dateien
   (mehr als ~100.000 Zeichen) gezielt mit `grep` suchen oder abschnittsweise
   lesen, statt alles auf einmal zu laden.

4. **Kurz berichten** - dem Nutzer in einem Satz sagen, welche Dateien
   umgewandelt wurden und wo die `.md`-Dateien liegen (bei Bedarf zum Download
   bereitstellen). Den Volltext nicht in den Chat kopieren, außer der Nutzer
   bittet ausdrücklich darum. Hat der Nutzer nur eine Datei angehängt, ohne
   etwas dazu zu schreiben, nach der Umwandlung einen kurzen Überblick über den
   Inhalt geben und fragen, was damit geschehen soll.

## Wann nicht umwandeln

- Reine Text-, Markdown- oder Code-Dateien: direkt lesen.
- Bilder, bei denen es um das Aussehen geht (Pläne, Fotos, Visualisierungen):
  direkt ansehen. MarkItDown liefert bei Bildern nur Metadaten.
- Wenn die Originaldatei **bearbeitet** werden soll (z. B. Excel-Formeln
  ändern, Word-Dokument mit Änderungsverfolgung überarbeiten): Markdown dient
  nur zum Lesen und Verstehen; die Änderung selbst in der Originaldatei mit dem
  passenden Werkzeug bzw. Skill (xlsx, docx, pptx, pdf) vornehmen.

## Unterstützte Formate

PDF, DOCX, PPTX, XLSX/XLS, CSV/TSV, HTML, JSON, XML, EPUB, MSG (Outlook), ZIP
(Inhalt wird durchlaufen), TXT/MD. Nicht unterstützt: Audio, Video, URLs
(bewusst, siehe Datenschutz), alte .doc/.ppt-Formate (ggf. lokal mit
LibreOffice nach .docx/.pptx konvertieren:
`soffice --headless --convert-to docx datei.doc`).
