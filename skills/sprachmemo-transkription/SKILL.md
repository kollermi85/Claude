---
name: sprachmemo-transkription
description: Transkribiert hochgeladene Audiodateien und Sprachmemos (iPhone-Sprachmemos .m4a, WhatsApp-Sprachnachrichten .opus/.ogg, .mp3, .wav, .aac, .flac, Video mit Ton .mp4/.mov) LOKAL in der Sandbox mit einem Whisper-Modell zu Text, ohne dass die Audiodaten an einen Transkriptionsdienst, eine Cloud-API oder ein anderes KI-Werkzeug gehen. IMMER verwenden, sobald der Nutzer eine Audio- oder Sprachdatei anhängt oder hochlädt, egal ob er "transkribieren", "abtippen", "verschriftlichen", "was sage ich da", "Protokoll aus dem Memo", "Aufgaben aus der Sprachnachricht" oder nur "schau dir das an" schreibt, und auch wenn er das Wort Transkription nicht verwendet.
---

# Sprachmemo-Transkription (lokal, datenschutzfreundlich)

Wandelt Sprachaufnahmen mit **Whisper** direkt in der Code-Ausführungsumgebung in Text um.
Es wird **kein** externer Transkriptionsdienst aufgerufen (keine OpenAI-API, kein Google, kein Upload-Konverter).
Aus dem Internet kommt nur beim ersten Lauf das **Modell** (die Gewichte). Audiodaten werden dabei
nie verschickt, sie bleiben in der Sandbox.

## Ablauf

### 1. Datei finden
Hochgeladene Dateien liegen normalerweise unter `/mnt/user-data/uploads/`. Wenn nicht, suchen:
```bash
find / -type f \( -iname '*.m4a' -o -iname '*.mp3' -o -iname '*.wav' -o -iname '*.opus' -o -iname '*.ogg' \
  -o -iname '*.aac' -o -iname '*.flac' -o -iname '*.mp4' -o -iname '*.mov' -o -iname '*.webm' \) \
  -newer /etc/hostname 2>/dev/null | grep -v -E '/(proc|sys|usr)/' | head
```

### 2. Abhängigkeiten installieren (nur beim ersten Mal pro Sitzung)
```bash
pip install -q sherpa-onnx av numpy faster-whisper 2>&1 | tail -1
```
Wenn `faster-whisper` nicht installierbar ist, ist das kein Problem: Das Skript nutzt dann automatisch `sherpa-onnx`.

### 3. Transkribieren
```bash
python <SKILL_DIR>/scripts/transcribe.py "/mnt/user-data/uploads/Memo.m4a" \
  --output-dir /mnt/user-data/outputs --timestamps
```
- `<SKILL_DIR>` ist der Ordner dieser SKILL.md.
- Mehrere Dateien auf einmal übergeben. Das Modell wird dann nur einmal geladen.
- Standard ist Deutsch (`--language de`). Bei anderen Sprachen `--language en` o.ä. oder `--language auto`.
- `--timestamps` bei Aufnahmen über ca. 2 Minuten verwenden. Bei kurzen Memos weglassen, dann gibt es Fließtext.
- Das Skript wählt die Engine selbst: zuerst faster-whisper (Hugging Face), und wenn Hugging Face gesperrt ist,
  automatisch sherpa-onnx (Whisper-Modelle von GitHub). Die Meldung `faster-whisper ... nicht verfügbar` ist
  normal und kein Fehler.

**Modellwahl** (`--model`):
| Modell | Download | Qualität Deutsch | Wann |
|---|---|---|---|
| `tiny` | ca. 120 MB | schwach | nur Tests |
| `base` | ca. 210 MB | mittel | sehr lange Aufnahmen (> 30 min), wenn es schnell gehen muss |
| `small` | ca. 640 MB | **gut** | **Standard** |
| `turbo` | ca. 560 MB | sehr gut | wenn `small` Fachbegriffe verhaut |
| `medium` | ca. 1,9 GB | sehr gut | nur mit viel Zeit |

Der erste Download von `small` dauert etwa 1 bis 2 Minuten. Die Transkription läuft auf der CPU ungefähr
in Echtzeit/5 bis Echtzeit/2 (ein 10-minütiges Memo braucht also ca. 2 bis 5 Minuten). Bei langen Dateien
den Befehl mit ausreichend Timeout starten und dem Nutzer vorher kurz sagen, dass es etwas dauert.

### 4. Ergebnis liefern
1. Die erzeugte `.md`-Datei lesen.
2. **Offensichtliche Hörfehler behutsam korrigieren**, wenn der Kontext eindeutig ist (Fachbegriffe aus Immobilien,
   Bau, Nachhaltigkeit wie "Energieausweis", "Photovoltaik", "Baubesprechung", Eigennamen). Nicht umformulieren und
   keine Inhalte erfinden. Unklare Stellen mit `[unverständlich]` oder `[?]` markieren.
3. Dem Nutzer das Transkript zeigen und die korrigierte Datei als Download bereitstellen.
4. Danach kurz anbieten, was sich typischerweise daraus machen lässt: Zusammenfassung, To-do-Liste,
   Aktenvermerk oder Besprechungsprotokoll, E-Mail-Entwurf. Wenn der Nutzer das beim Hochladen schon verlangt hat,
   direkt erledigen. Für Geschäftstexte den Skill `schreibstil-mk` verwenden, falls vorhanden.

## Datenschutz: was du dem Nutzer ehrlich sagen kannst
- Die Umwandlung Audio → Text passiert vollständig lokal in der Sandbox mit einem Open-Source-Modell.
- Die Audiodatei wird an **keinen** weiteren Dienst geschickt.
- Aus dem Netz geladen wird nur das Modell (öffentliche Dateien von Hugging Face bzw. GitHub).
- Die Datei selbst wurde aber in den Claude-Chat hochgeladen und liegt damit bei Anthropic wie jeder andere Anhang.
  Wer das vermeiden möchte, kann `scripts/transcribe.py` auf dem eigenen Rechner ausführen (siehe README.md im
  Skill-Ordner) und nur den fertigen Text teilen oder ganz lokal behalten.

## Fehlerbehebung
- **`Keine Engine verfügbar`**: Die Sandbox hat keinen Netzzugang zu GitHub oder Hugging Face. Dem Nutzer sagen,
  dass unter Einstellungen → Funktionen der Netzwerkzugang für die Code-Ausführung aktiviert sein muss, oder die
  lokale Variante aus der README empfehlen.
- **Datei lässt sich nicht dekodieren**: `python -c "import av; print(av.open('DATEI').streams)"` zeigt, ob eine
  Audiospur da ist. Bei exotischen Formaten zuerst mit `ffmpeg -i DATEI -ar 16000 -ac 1 out.wav` umwandeln, falls
  ffmpeg vorhanden ist.
- **Viel Wiederholung oder Unsinn im Text**: Meist ist es sehr leise oder es läuft Musik im Hintergrund.
  `--model turbo` probieren.
- **Falsche Sprache**: `--language` explizit setzen.
