# Voice Assistant Setup Guide

This walkthrough is intentionally explicit so every teammate—regardless of comfort level with command lines—can get the project running the same way. Follow each numbered checklist item in order and check it off before moving on.

## 0. Before You Start

1. **Install Python 3.11+** – `python3 --version` should print `3.11.x` or newer.
2. **Install Git** – `git --version` should show `git version ...`.
3. **macOS users:** `brew install portaudio`  
   **Ubuntu/Debian:** `sudo apt install portaudio19-dev python3-venv`  
   **Windows:** use [pipwin](https://github.com/leifgehrmann/pipwin) after Python is installed: `pip install pipwin && pipwin install pyaudio`.
4. **Create/OpenAI + ElevenLabs accounts** and have API keys ready. We never commit them to git.

> If any command above errors, resolve it first—every later step depends on these prerequisites.

## 1. Clone the Repository

```bash
cd ~/code  # or wherever you keep projects
git clone git@github.com:czyber/voice-assistant.git
cd voice-assistant
```

Confirm you are inside the repo root with `pwd`.

## 2. Create the Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
```

You should now see `(.venv)` prefixed in your terminal prompt. Keep the environment active while working on the project.

## 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

If PyAudio fails to build, revisit Step 0 and ensure the PortAudio headers are installed for your platform.

## 4. Create Your Local Config

1. Copy the template: `cp config.json config.local.json`
2. Open `config.local.json` in your editor and fill in the blanks:

```json
{
  "openai": {
    "api_key": "sk-...your key...",
    "organization": "org-...optional..."
  },
  "elevenlabs": {
    "api_key": "eleven-...your key..."
  }
}
```

3. Save the file. Git ignores `config.local.json`, so your keys stay local.

## 5. Verify the Installation

1. **Microphone sanity check (requires active virtual environment):**
   ```bash
   python -m audio_input.microphone
   ```
   - Press Enter when prompted.  
   - Speak normally for ~5 seconds.  
   - The script saves `audio_input/test_recording.wav`. Play it back with your OS audio player.
2. **Playground demo (optional but recommended):**
   ```bash
   python -m core.playground
   ```
   Watch the console logs to confirm that transcription and TTS requests reach the APIs.

> If any step fails, copy the error message into the group chat. Mention which numbered step you were on so we can debug quickly.

## 6. Day-to-Day Workflow

1. Activate the venv: `source .venv/bin/activate`
2. Pull latest `main`: `git switch main && git pull`
3. Create a task branch: `git switch -c feature/<your-name>-<task>`
4. Run `pytest` before pushing a branch or opening a PR.

## Logging Controls

The project now emits detailed, structured logs for every subsystem. You can tune verbosity without code changes:

| Env Var | What it does | Example |
| --- | --- | --- |
| `VOICE_ASSISTANT_LOG_LEVEL` | Adjusts severity (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `export VOICE_ASSISTANT_LOG_LEVEL=DEBUG` |
| `VOICE_ASSISTANT_LOG_FILE` | Writes the same logs to a file (directories auto-created) | `export VOICE_ASSISTANT_LOG_FILE=~/voice-assistant/logs/run.log` |
| `VOICE_ASSISTANT_LOG_FORMAT` | Override the default format string | `export VOICE_ASSISTANT_LOG_FORMAT="%(asctime)s %(levelname)s %(message)s"` |

All logs include a run identifier (`run=abcd1234`) so multiple teammates can correlate their terminal output when pairing.

## Troubleshooting Cheat Sheet

- **`ModuleNotFoundError: No module named 'pyaudio'`** – PortAudio headers missing. Re-run the platform-specific command in Step 0, then `pip install pyaudio`.
- **`openai.error.AuthenticationError`** – Your API key is empty or invalid. Re-open `config.local.json` and confirm there are no trailing spaces.
- **`OSError: [Errno -9996] Invalid input device (no default output device)`** – On macOS, open *System Settings → Privacy & Security → Microphone* and grant terminal access, then retry.
- **Logs too quiet/noisy** – Export `VOICE_ASSISTANT_LOG_LEVEL` before running your script (see table above).

Still stuck? Tag the tech lead in chat with the exact command and the full error snippet.
