# Voice Assistant – Sprint 1

Welcome to the team project! This repository contains the shared scaffolding for our voice assistant. Each teammate owns one segment of the audio pipeline, so our main job this sprint is to keep the interfaces and folder structure predictable.

## TL;DR Setup

```bash
# 1. Grab dependencies
# macOS only: install PortAudio headers first
brew install portaudio

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Add API keys
cp config.json config.local.json  # keep secrets out of git
# edit config.local.json with your keys
```

> Need help with Git? See `docs/git_workflow.md`.

## Pipeline Overview

You speak → `audio_input` (Microphone) → `audio_output/stt` (Whisper STT) → `core` (LLM logic + tools) → `tools` (Spotify actions) → `audio_output/tts` (OpenAI TTS) → speakers.

We share strongly typed contracts defined in `core/interfaces.py`. Import these when building your component.

## Repository Map

- `core/` – shared data classes and interfaces
- `audio_input/` – microphone capture code (Physics Student)
- `audio_output/` – speech-to-text and text-to-speech (STT/TTS Person)
- `tools/` – integrations like Spotify (Integration Engineer)
- `hardware/` – enclosure CAD files and docs (3D Artist)
- `docs/` – project docs, personality, workflows
- `tests/` – automated checks (pytest)

## Configuration

- Copy `config.json` to `config.local.json` and fill in your real keys.
- Never commit secrets; the template lives in git, real values stay local.
- Spotify redirect URI **must** be `http://localhost:8888/callback`.

### Platform notes

- **macOS (Apple Silicon/Intel):** `brew install portaudio` before installing PyAudio.
- **Ubuntu/Debian:** `sudo apt install portaudio19-dev` prior to `pip install -r requirements.txt`.
- **Windows:** Use `pip install pipwin && pipwin install pyaudio` if the wheel build fails.

## Working Agreements

1. **Branch per task** – no direct commits on `main`.
2. **Follow the interfaces** in `core/interfaces.py`.
3. **Keep modules self-contained** so they can be reused by the orchestrator.
4. **Document surprises** in `docs/` so everyone stays in sync.

## Running Tests

```bash
pytest tests
```

We will add more integration coverage once every module has a shim implementation.

### Manual audio check

```bash
python -m audio_input.microphone
```

Press Enter, speak for 5 seconds, and confirm `test_recording.wav` sounds clear.

## Need Help?

- Interface questions → tag Tech Lead
- Spotify auth issues → start in the Spotipy quick start guide
- Hardware constraints → coordinate CAD decisions in `hardware/assembly_guide.md`

Let's keep communication async-friendly: post updates in the shared chat when you push a branch or hit a blocker.
