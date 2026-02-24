# Basic Pitch Transcription Service

Lightweight Flask microservice that wraps [basic-pitch](https://github.com/spotify/basic-pitch) for audio-to-MIDI transcription. Runs in a separate Python 3.12 environment because basic-pitch does not yet support Python 3.13+.

## Setup

1. **Requires Python 3.12** (install via `winget install Python.Python.3.12`)

2. Create a virtual environment:
   ```
   py -3.12 -m venv services/basic-pitch/venv
   ```

3. Install dependencies (two steps — basic-pitch needs `--no-deps` to skip its TensorFlow requirement since we use the ONNX backend on Windows):
   ```
   services\basic-pitch\venv\Scripts\pip install --no-deps basic-pitch
   services\basic-pitch\venv\Scripts\pip install -r services\basic-pitch\requirements.txt
   ```

4. Start the service:
   ```
   services\basic-pitch\start.bat
   ```
   Or manually:
   ```
   services\basic-pitch\venv\Scripts\activate
   python services\basic-pitch\app.py
   ```

The service runs at **http://localhost:8765**.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Returns `{"status": "ok"}` if the service is running |
| POST | `/transcribe` | Upload audio file (field: `file`), returns MIDI file |

## Supported Audio Formats

`.wav`, `.mp3`, `.m4a`, `.ogg`, `.flac`

Max file size: 50 MB.

## Notes

- Uses the **ONNX backend** — TensorFlow is not required on Windows.
- The first transcription request will be slow (~30s) as basic-pitch loads the ML model.
- Subsequent requests are faster (model stays in memory).
- Long audio files (>5 minutes) may take 30+ seconds to process.
- When basic-pitch adds Python 3.13 support, this service can be replaced with direct integration in the main app. See `app/audio/transcribe.py` for the compatibility flag.
