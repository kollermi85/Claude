---
name: datei-zu-markdown
description: Wandelt jede angehängte oder hochgeladene Datei (PDF, Word/DOCX, PowerPoint/PPTX, Excel/XLSX/XLS, CSV, HTML, JSON, EPUB, Outlook-MSG, ZIP) zuerst lokal mit Microsoft MarkItDown in Markdown um, bevor damit gearbeitet wird - ohne Cloud-Konverter oder KI-Dienste. IMMER verwenden, sobald der Nutzer eine Datei anhängt oder hochlädt, egal ob er zusammenfassen, prüfen, vergleichen, Zahlen herausziehen, Fragen dazu beantworten oder nur "schau dir das an" möchte - auch wenn er Markdown nicht erwähnt. Ebenso bei ausdrücklichen Anfragen wie "in Markdown umwandeln", "als .md", "Text aus der PDF holen". Legt die Markdown-Notiz anschließend im Obsidian-Vault des Nutzers (Google Drive) im passenden Arbeits- oder Privatprojekt ab und fragt nach, wenn die Datei keinem Projekt eindeutig zuzuordnen ist.
---

# Datei zu Markdown (lokal)

Angehängte Dateien werden zuerst in Markdown umgewandelt und danach wird mit
dem Markdown gearbeitet. Markdown ist kompakt, gut durchsuchbar und behält
Überschriften und Tabellen bei - so lassen sich auch lange Gutachten,
Baubeschreibungen, Leistungsverzeichnisse oder Kostenaufstellungen vollständig
und ohne Textverlust auswerten.

## Datenschutz - warum die Umwandlung lokal bleibt

Der Nutzer möchte ausdrücklich, dass keine Dokumentinhalte an externe Dienste
gehen. Deshalb:

- MarkItDown nur ohne `llm_client`, ohne `docintel_endpoint` (Azure) und ohne
  Plugins verwenden - genau so, wie es `scripts/convert.py` tut.
- Audio- und Videodateien nicht umwandeln (die Transkription liefe über einen
  Google-Dienst) und keine URLs/YouTube-Links abrufen.
- Keine Online-Konverter, OCR-APIs oder sonstigen Webdienste für Dateiinhalte.
- Erlaubte Verbindungen nach außen: `pip install` von PyPI, falls MarkItDown
  fehlt, und das Ablegen der fertigen `.md` im **eigenen** Obsidian-Vault des
  Nutzers in Google Drive (vom Nutzer so gewünscht). Dateien dort nie teilen
  (`share_file`), Originaldateien nicht hochladen.

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

4. **Im Obsidian-Vault ablegen** - siehe nächster Abschnitt.

5. **Kurz berichten** - in ein, zwei Sätzen sagen, welche Dateien umgewandelt
   und wo sie abgelegt wurden (Ordnerpfad im Vault). Den Volltext nicht in den
   Chat kopieren, außer der Nutzer bittet darum. Hat der Nutzer nur eine Datei
   angehängt, ohne etwas dazu zu schreiben, zusätzlich einen kurzen Überblick
   über den Inhalt geben und fragen, was damit geschehen soll.

## Ablage im Obsidian-Vault (Google Drive)

Der Vault des Nutzers liegt in Google Drive, Ordner **`Obsidian-Vault`**
(innerhalb von `Claude `), Ordner-ID `1rrfAiJPAi2r_xvkY1Wqsbrqjyf3MMHEK`.
Falls die ID nicht mehr passt: mit `search_files`
`title = 'Obsidian-Vault' and mimeType = 'application/vnd.google-apps.folder'`
neu suchen. Obsidian synchronisiert den Ordner über Google Drive, daher
erscheinen dort abgelegte `.md`-Dateien direkt als Notizen.

Aufbau des Vaults:

| Ordner | Inhalt |
|---|---|
| `00 Inbox` | Neues, noch nicht Einsortiertes |
| `10 Projekte/Arbeit/<Projekt>` | berufliche Projekte, z. B. `FH3`, `AQ` (weitere folgen) |
| `10 Projekte/Privat/<Projekt>` | private Projekte (z. B. Wohnung, Garten, Reise, Finanzen) |
| `20 Wissen` | Nachhaltigkeit, ESG, mentale Themen, Bücher, Podcasts |
| `30 Gesundheit` | Befunde, Ernährung, Autoimmunerkrankung |
| `40 Journal` | Tagesnotizen |
| `90 Vorlagen` | Notizvorlagen |

### a) Projekt ermitteln

1. Aktuelle Projekte laden - aus **beiden** Bereichen, per `search_files`
   `(parentId = '1eSy1NHKGFVpkuqFjR5LrJklvaCKmv1VW' or parentId = '171TlBlbPvIb6Jj-rZf8K0H50VXE-1Hv9') and mimeType = 'application/vnd.google-apps.folder'`
   (erste ID = `10 Projekte/Arbeit`, zweite = `10 Projekte/Privat`; falls die
   IDs nicht mehr passen, die Ordner über ihren Namen unter `10 Projekte`
   suchen). Anhand des `parentId` jedes Treffers festhalten, ob es ein
   Arbeits- oder ein Privatprojekt ist. In jedem Projektordner liegt eine
   Projektnotiz `<Projekt>.md`; ihr Frontmatter enthält `aliases` und
   `stichworte` (Adresse, EZ/KG, Projektcode, Beteiligte ...). Die Notizen
   mit `read_file_content` lesen - die Projektliste ändert sich, deshalb
   jedes Mal neu laden statt sie auswendig anzunehmen.
2. Abgleichen: Nachricht des Nutzers, Dateiname und Anfang des umgewandelten
   Markdowns (Titel, Betreff, Adresse) gegen Projektnamen, Aliase und
   Stichworte prüfen.
3. Entscheiden:
   - **Genau ein Projekt passt eindeutig** (Nutzer nennt es, oder Name /
     Stichwort steht im Dateinamen oder Dokumentkopf): dort ablegen und im
     Bericht nennen, damit der Nutzer widersprechen kann.
   - **Kein oder mehr als ein Treffer: nachfragen, nicht raten.** Eine
     falsch einsortierte Notiz fällt in Obsidian kaum auf und ist später
     schwer wiederzufinden - eine kurze Rückfrage kostet weniger. Antwortmöglichkeiten
     anbieten: die vorhandenen Projekte mit Bereich gekennzeichnet (z. B.
     „FH3 (Arbeit)“, „Wohnung (Privat)“), „Neues Projekt anlegen“,
     `00 Inbox`, sowie `20 Wissen` bzw. `30 Gesundheit`, wenn der Inhalt
     danach aussieht (z. B. Fachartikel bzw. Laborbefund). Bei
     Gleichnamigkeit in beiden Bereichen immer nachfragen.
   - Private Dokumente (Mietvertrag der eigenen Wohnung, Versicherung,
     Arztbrief) nie automatisch in einen Arbeitsordner legen und umgekehrt -
     bei Zweifel, ob etwas beruflich oder privat ist, fragen. Wenn ein
     Rückfrage-Werkzeug mit Auswahlknöpfen verfügbar ist, dieses verwenden.

### b) Als Obsidian-Notiz umwandeln

Die Umwandlung mit Obsidian-Kopf wiederholen bzw. gleich so ausführen:

```bash
python <skill-pfad>/scripts/convert.py <datei> --obsidian --projekt FH3
```

`--obsidian` erzeugt `<Dateiname>.md` mit Frontmatter (`typ`, `quelle`,
`format`, `konvertiert`, `projekt: "[[FH3]]"`, `tags`). Der Projekt-Link sorgt
dafür, dass das Dokument in der Projektnotiz unter den Rückverweisen
(Backlinks) auftaucht. Ohne Projekt `--projekt` weglassen; für Wissens- oder
Gesundheitsablage `--typ Wissen` bzw. `--typ Gesundheit` setzen.

### c) Hochladen

Mit dem Google-Drive-Werkzeug `create_file`:

- `title`: Dateiname inkl. `.md`
- `parentId`: ID des Zielordners
- `textContent`: Inhalt der erzeugten `.md`
- `contentMimeType`: `text/markdown`
- `disableConversionToGoogleType`: **true** - sonst wird daraus ein
  Google-Dokument, das Obsidian nicht lesen kann.

Vorher per `search_files` (`parentId = '<Ziel>' and title = '<Name>.md'`)
prüfen, ob es die Notiz schon gibt. Wenn ja, den Nutzer fragen; ohne Antwort
mit angehängtem Datum ablegen (`<Name> 2026-09-23.md`), nie stillschweigend
doppelt.

### d) Neues Projekt anlegen

Wenn der Nutzer ein neues Projekt nennt, zuerst klären, ob es ein
**Arbeits- oder Privatprojekt** ist (sofern nicht offensichtlich). Dann unter
`10 Projekte/Arbeit` bzw. `10 Projekte/Privat` einen Ordner `<Projekt>` anlegen (`create_file`, `contentMimeType`
`application/vnd.google-apps.folder`) und darin die Projektnotiz
`<Projekt>.md` nach `references/projekt-vorlage.md`. Nach Stichworten
fragen (bei Arbeit: Adresse, EZ/KG, Beteiligte; bei Privat: was das Projekt
ausmacht) und sie ins Frontmatter schreiben; bei Privatprojekten
`bereich: Privat` statt `bereich: Arbeit` setzen - sie
machen die automatische Zuordnung künftiger Dateien möglich.

### Wenn Google Drive nicht verfügbar ist

Ist der Google-Drive-Connector in der Sitzung nicht aktiv, die `.md`-Dateien
zum Download bereitstellen und den Zielordner im Vault nennen, damit der
Nutzer sie selbst hineinziehen kann. Darauf hinweisen, dass der Connector in
den Einstellungen aktiviert werden kann.

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
