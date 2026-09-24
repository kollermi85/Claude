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

### 2. Vorbereiten (kurz, jeweils eigener Befehl)
```bash
pip install -q sherpa-onnx av numpy 2>&1 | tail -1
python <SKILL_DIR>/scripts/transcribe.py --check
```
- `<SKILL_DIR>` ist der Ordner dieser SKILL.md.
- `faster-whisper` hier **nicht** installieren: In der Sandbox ist Hugging Face gesperrt, das kostet nur Zeit.
- Meldet `--check` **`NETZ_FEHLT`**, sofort abbrechen und dem Nutzer den Abschnitt „Netzwerkzugang“ unten erklären.
  Nicht weiter probieren.

### 3. Im Hintergrund transkribieren und den Fortschritt abfragen
Der erste Lauf lädt ca. 640 MB Modell und entpackt es (1–3 Minuten). Danach folgt die Transkription.
Damit die Antwort nicht an einer Zeitgrenze abbricht, **immer im Hintergrund starten** und nur kurz nachsehen:
```bash
cd /mnt/user-data/uploads && nohup python <SKILL_DIR>/scripts/transcribe.py "Memo.m4a" \
  --engine sherpa --output-dir /mnt/user-data/outputs --timestamps > /tmp/sprachmemo.log 2>&1 &
echo gestartet
```
Danach wiederholt (jeder Aufruf dauert höchstens ca. 45 s):
```bash
sleep 40; tail -n 3 /tmp/sprachmemo.log
```
- Fertig ist es, sobald eine Zeile mit `OK:` erscheint. Bei `FEHLER` den Log ganz lesen.
- Zwischendurch dem Nutzer knapp den Stand nennen („Modell wird geladen, 60 %“, „Transkription bei 03:10 von 08:00“).
- Mehrere Dateien in **einem** Aufruf übergeben. Das Modell wird dann nur einmal geladen.
- Standard ist Deutsch (`--language de`). Bei anderen Sprachen `--language en` o.ä. oder `--language auto`.
- `--timestamps` bei Aufnahmen über ca. 2 Minuten verwenden. Bei kurzen Memos weglassen, dann gibt es Fließtext.
- Jeder neue Chat hat eine frische Sandbox, das Modell wird dort also erneut geladen.

**Modellwahl** (`--model`):
| Modell | Download | Qualität Deutsch | Wann |
|---|---|---|---|
| `tiny` | ca. 120 MB | schwach | nur Tests |
| `base` | ca. 210 MB | mittel | sehr lange Aufnahmen (> 30 min), wenn es schnell gehen muss |
| `small` | ca. 640 MB | **gut** | **Standard** |
| `turbo` | ca. 560 MB | sehr gut | wenn `small` Fachbegriffe verhaut |
| `medium` | ca. 1,9 GB | sehr gut | nur mit viel Zeit |

Die Transkription läuft auf der CPU ungefähr in Echtzeit/5 bis Echtzeit/2. Ein 10-minütiges Memo braucht also
ca. 2 bis 5 Minuten.

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

## Netzwerkzugang (wenn `NETZ_FEHLT`)
Dem Nutzer Schritt für Schritt erklären: claude.ai im Browser → Profil unten links → **Einstellungen** →
**Funktionen** (*Capabilities*) → **Code-Ausführung und Dateierstellung** einschalten → bei Netzwerkzugang
**„Paketmanager und bestimmte Domains“** wählen und `github.com` sowie `release-assets.githubusercontent.com`
hinzufügen (oder „Alle Domains“). Danach einen **neuen Chat** starten.

## Fehlerbehebung
- **Datei lässt sich nicht dekodieren**: `python -c "import av; print(av.open('DATEI').streams)"` zeigt, ob eine
  Audiospur da ist.
- **Download bricht ab / sehr langsam**: mit `--model base` erneut starten (ca. 210 MB statt 640 MB).
- **Viel Wiederholung oder Unsinn im Text**: Meist ist es sehr leise oder es läuft Musik im Hintergrund.
  `--model turbo` probieren.
- **Falsche Sprache**: `--language` explizit setzen.
