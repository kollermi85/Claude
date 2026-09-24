# Sprachmemo-Transkription

Claude-Skill zum lokalen Transkribieren von Sprachmemos mit Whisper. Es gibt keinen Cloud-Transkriptionsdienst und keine API-Kosten.

## In Claude installieren
1. `sprachmemo-transkription.zip` herunterladen (liegt im Ordner `dist/` des Repos).
2. In claude.ai: **Einstellungen → Funktionen (Capabilities)** → Code-Ausführung aktivieren und bei Netzwerkzugang
   mindestens GitHub erlauben (damit das Modell einmalig geladen werden kann).
3. Unter **Skills** → „Skill hochladen“ → die ZIP-Datei auswählen.
4. Im Chat einfach die Sprachmemo-Datei anhängen, z.B. mit „Bitte transkribieren“.

iPhone-Tipp: In der App Sprachmemos auf die Aufnahme tippen → „…“ → „Teilen“ → „In Dateien sichern“, dann in der
Claude-App über die Büroklammer anhängen.

## Ganz ohne Upload: auf dem eigenen Rechner
Nach dem einmaligen Modell-Download läuft das komplett offline. Die Aufnahme verlässt dann nie das Gerät.
```bash
pip install -r requirements.txt
python scripts/transcribe.py ~/Downloads/Memo.m4a --timestamps           # erster Lauf lädt das Modell
python scripts/transcribe.py ~/Downloads/Memo2.m4a --offline             # danach komplett ohne Netz
```
Die Transkripte landen als Markdown in `./transkripte/`. Dort kann man sie z.B. in Obsidian ablegen oder nur den
Text in Claude einfügen.

Modelle werden in `~/.cache/sprachmemo-transkription` (sherpa-onnx) bzw. `~/.cache/huggingface` (faster-whisper)
gespeichert.
