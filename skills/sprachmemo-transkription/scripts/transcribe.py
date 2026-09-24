#!/usr/bin/env python3
"""Transkribiert Sprachmemos (m4a, mp3, wav, ...) lokal mit Whisper.

Die Audiodaten verlassen die Umgebung nicht: Es wird kein Cloud-Dienst und
keine Transkriptions-API aufgerufen. Nur beim allerersten Lauf wird das
Whisper-Modell (die Gewichte, nicht die Audiodatei) einmalig heruntergeladen
und danach aus dem Cache verwendet.

Zwei Engines, gleiche Whisper-Modelle:
  - faster-whisper  (Modelle von Hugging Face)
  - sherpa-onnx     (Modelle von GitHub-Releases; Fallback, wenn Hugging Face
                     gesperrt ist, wie z.B. in der Claude-Sandbox)
Mit --engine auto (Standard) wird faster-whisper versucht und bei Problemen
automatisch auf sherpa-onnx gewechselt.

Nutzung:
    python transcribe.py memo.m4a
    python transcribe.py memo1.m4a memo2.m4a --model small --language de
    python transcribe.py memo.m4a --timestamps --output-dir transkripte
    python transcribe.py memo.m4a --offline   # nur bereits geladene Modelle nutzen
"""

import argparse
import os
import sys
import tarfile
import time
import urllib.request
from datetime import timedelta
from pathlib import Path

SUPPORTED_SUFFIXES = {
    ".m4a", ".mp3", ".wav", ".aac", ".ogg", ".opus", ".flac",
    ".mp4", ".mov", ".webm", ".amr", ".caf", ".qta",
}
SAMPLE_RATE = 16000
CACHE_DIR = Path(os.environ.get("SPRACHMEMO_CACHE", Path.home() / ".cache" / "sprachmemo-transkription"))
SHERPA_BASE = "https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models"


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def fmt_ts(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds))).rjust(8, "0")


# --------------------------------------------------------------------------
# Engine 1: faster-whisper
# --------------------------------------------------------------------------
class FasterWhisperEngine:
    name = "faster-whisper"

    def __init__(self, model: str, offline: bool):
        if offline:
            os.environ["HF_HUB_OFFLINE"] = "1"
        from faster_whisper import WhisperModel
        self.model = WhisperModel(model, device="cpu", compute_type="int8")

    def transcribe(self, src: Path, language: str | None) -> tuple[list[tuple[float, str]], float, str]:
        segments, info = self.model.transcribe(
            str(src),
            language=language,
            vad_filter=True,  # Stille überspringen -> schneller, weniger Halluzinationen
            beam_size=5,
        )
        out = [(s.start, s.text.strip()) for s in segments if s.text.strip()]
        return out, info.duration, info.language


# --------------------------------------------------------------------------
# Engine 2: sherpa-onnx (Whisper als ONNX, Modelle von GitHub)
# --------------------------------------------------------------------------
def download(url: str, dest: Path) -> None:
    log(f"Lade {url} ...")
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url) as resp, open(tmp, "wb") as fh:
        while chunk := resp.read(1 << 20):
            fh.write(chunk)
    tmp.rename(dest)


def ensure_sherpa_model(model: str, offline: bool) -> Path:
    model_dir = CACHE_DIR / f"sherpa-onnx-whisper-{model}"
    needed = [f"{model}-encoder.int8.onnx", f"{model}-decoder.int8.onnx", f"{model}-tokens.txt"]
    if all((model_dir / n).exists() for n in needed):
        return model_dir
    if offline:
        raise RuntimeError(f"Modell {model} nicht im Cache ({model_dir}) und --offline gesetzt")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    url = f"{SHERPA_BASE}/sherpa-onnx-whisper-{model}.tar.bz2"
    log(f"Lade Whisper-Modell '{model}' einmalig von GitHub (nur Modell, keine Audiodaten) ...")
    # Streamend entpacken und nur die int8-Dateien behalten (spart die Hälfte an Speicher)
    with urllib.request.urlopen(url) as resp, tarfile.open(fileobj=resp, mode="r|bz2") as tar:
        for member in tar:
            base = Path(member.name).name
            if member.isfile() and base in needed:
                member.name = f"{model_dir.name}/{base}"
                tar.extract(member, CACHE_DIR)
    missing = [n for n in needed if not (model_dir / n).exists()]
    if missing:
        raise RuntimeError(f"Modell-Download unvollständig, es fehlt: {missing}")
    return model_dir


def ensure_vad(offline: bool) -> Path:
    path = CACHE_DIR / "silero_vad.onnx"
    if not path.exists():
        if offline:
            raise RuntimeError(f"VAD-Modell nicht im Cache ({path}) und --offline gesetzt")
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        download(f"{SHERPA_BASE}/silero_vad.onnx", path)
    return path


def load_audio(src: Path):
    """Dekodiert beliebige Audio-/Videodateien lokal zu 16 kHz Mono float32."""
    import av
    import numpy as np

    chunks = []
    with av.open(str(src)) as container:
        resampler = av.AudioResampler(format="flt", layout="mono", rate=SAMPLE_RATE)
        for frame in container.decode(audio=0):
            for out in resampler.resample(frame):
                chunks.append(out.to_ndarray().reshape(-1))
        for out in resampler.resample(None):
            chunks.append(out.to_ndarray().reshape(-1))
    return np.concatenate(chunks).astype(np.float32) if chunks else np.zeros(0, dtype=np.float32)


class SherpaEngine:
    name = "sherpa-onnx"

    def __init__(self, model: str, offline: bool):
        import sherpa_onnx
        self.sherpa = sherpa_onnx
        self.model_dir = ensure_sherpa_model(model, offline)
        self.vad_path = ensure_vad(offline)
        self.model = model
        self._recognizers = {}

    def _recognizer(self, language: str):
        if language not in self._recognizers:
            d, m = self.model_dir, self.model
            self._recognizers[language] = self.sherpa.OfflineRecognizer.from_whisper(
                encoder=str(d / f"{m}-encoder.int8.onnx"),
                decoder=str(d / f"{m}-decoder.int8.onnx"),
                tokens=str(d / f"{m}-tokens.txt"),
                language=language,  # "" = automatische Erkennung
                task="transcribe",
                num_threads=max(1, (os.cpu_count() or 2) - 1),
            )
        return self._recognizers[language]

    def _speech_segments(self, samples):
        config = self.sherpa.VadModelConfig()
        config.silero_vad.model = str(self.vad_path)
        config.silero_vad.min_silence_duration = 0.4
        config.silero_vad.max_speech_duration = 25  # Whisper verarbeitet max. 30 s am Stück
        config.sample_rate = SAMPLE_RATE
        vad = self.sherpa.VoiceActivityDetector(config, buffer_size_in_seconds=120)
        window = config.silero_vad.window_size
        segments = []

        def drain():
            while not vad.empty():
                segments.append((vad.front.start / SAMPLE_RATE, vad.front.samples))
                vad.pop()

        for i in range(0, len(samples), window):
            vad.accept_waveform(samples[i:i + window])
            drain()
        vad.flush()
        drain()
        return segments

    def transcribe(self, src: Path, language: str | None) -> tuple[list[tuple[float, str]], float, str]:
        samples = load_audio(src)
        recognizer = self._recognizer(language or "")
        out = []
        for start, seg in self._speech_segments(samples):
            stream = recognizer.create_stream()
            stream.accept_waveform(SAMPLE_RATE, seg)
            recognizer.decode_stream(stream)
            text = stream.result.text.strip()
            if text:
                out.append((start, text))
        return out, len(samples) / SAMPLE_RATE, language or "auto"


# --------------------------------------------------------------------------
def load_engine(engine: str, model: str, offline: bool):
    order = {"auto": [FasterWhisperEngine, SherpaEngine],
             "faster-whisper": [FasterWhisperEngine],
             "sherpa": [SherpaEngine]}[engine]
    errors = []
    for cls in order:
        try:
            log(f"Lade Modell '{model}' mit {cls.name} ...")
            return cls(model, offline)
        except Exception as e:  # noqa: BLE001 - nächste Engine probieren
            errors.append(f"{cls.name}: {type(e).__name__}: {str(e).splitlines()[0] if str(e) else ''}")
            log(f"  -> nicht verfügbar ({errors[-1]})")
    raise RuntimeError("Keine Engine verfügbar:\n  " + "\n  ".join(errors))


def to_markdown(src: Path, segments, duration: float, language: str, engine: str, model: str,
                timestamps: bool) -> str:
    if timestamps:
        body = "\n".join(f"[{fmt_ts(start)}] {text}" for start, text in segments)
    else:
        body = " ".join(text for _, text in segments)
    return (
        f"# Transkript: {src.stem}\n\n"
        f"- Quelldatei: `{src.name}`\n"
        f"- Dauer: {fmt_ts(duration)}\n"
        f"- Sprache: {language}\n"
        f"- Modell: Whisper `{model}` via {engine} (lokal)\n\n"
        f"## Text\n\n{body or '_(keine Sprache erkannt)_'}\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+", help="Audiodateien")
    parser.add_argument("--model", default="small",
                        help="Whisper-Modell: tiny, base, small (Standard), medium, turbo")
    parser.add_argument("--language", default="de",
                        help="Sprachcode, z.B. de, en. 'auto' für automatische Erkennung (Standard: de)")
    parser.add_argument("--engine", choices=["auto", "faster-whisper", "sherpa"], default="auto")
    parser.add_argument("--timestamps", action="store_true", help="Zeitmarken pro Abschnitt ausgeben")
    parser.add_argument("--output-dir", default="transkripte", help="Zielordner (Standard: transkripte)")
    parser.add_argument("--offline", action="store_true",
                        help="Keinerlei Netzwerkzugriff; Modell muss bereits lokal vorhanden sein")
    args = parser.parse_args()

    language = None if args.language == "auto" else args.language
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        engine = load_engine(args.engine, args.model, args.offline)
    except RuntimeError as e:
        log(f"FEHLER: {e}")
        return 2

    exit_code = 0
    for f in args.files:
        src = Path(f)
        if not src.exists():
            log(f"FEHLER: Datei nicht gefunden: {src}")
            exit_code = 1
            continue
        if src.suffix.lower() not in SUPPORTED_SUFFIXES:
            log(f"WARNUNG: Unbekanntes Format {src.suffix}, versuche es trotzdem ...")
        start = time.time()
        try:
            segments, duration, lang = engine.transcribe(src, language)
        except Exception as e:  # noqa: BLE001 - Fehler pro Datei melden, Rest weiter verarbeiten
            log(f"FEHLER bei {src.name}: {e}")
            exit_code = 1
            continue
        dest = output_dir / f"{src.stem}.md"
        dest.write_text(to_markdown(src, segments, duration, lang, engine.name, args.model, args.timestamps),
                        encoding="utf-8")
        log(f"OK: {src.name} -> {dest} ({fmt_ts(duration)} Audio, {time.time() - start:.0f}s)")
        print(dest)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
