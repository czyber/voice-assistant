# Git Workflow – Voice Assistant Team

Our goal: keep `main` always stable while making it simple for everyone with minimal Git experience.

## Before You Start

1. Install Git and set your name/email:
   ```bash
   git config --global user.name "Your Name"
   git config --global user.email "you@example.com"
   ```
2. Clone the repo (first time only):
   ```bash
   git clone <repo-url>
   cd voice-assistant
   ```
3. Pull latest changes before starting new work:
   ```bash
   git pull origin main
   ```

## Daily Flow

1. **Create a branch for your task**
   ```bash
   git checkout -b feature/<your-task>
   # e.g. feature/microphone-capture
   ```
2. **Do your work** (edit files, run tests).
3. **View what changed**
   ```bash
   git status
   git diff              # optional detailed view
   ```
4. **Stage files** you want to include in the commit:
   ```bash
   git add path/to/file.py
   ```
5. **Write a clear commit message**
   ```bash
   git commit -m "Add microphone capture that returns AudioChunk"
   ```
6. **Sync with main** before pushing (avoids conflicts later):
   ```bash
   git checkout main
   git pull origin main
   git checkout feature/<your-task>
   git merge main        # or `git rebase main` if you're comfortable
   ```
7. **Push your branch**
   ```bash
   git push -u origin feature/<your-task>
   ```
8. **Open a pull request** on GitHub:
   - Title: brief summary (e.g., "Add Whisper STT adapter")
   - Description: what changed, how to test, screenshots/logs if relevant.

## Code Review Checklist

- Interfaces from `core/interfaces.py` are respected.
- Tests or manual verification steps are documented.
- No secrets or large binaries committed.
- `pytest` (or your module-specific checks) pass locally.

## Handling Feedback

1. Make requested changes on the same branch.
2. `git add` and `git commit --amend` *or* create new commits.
3. `git push` (use `git push --force-with-lease` if you amended).

## When Merging

1. Ensure the PR has at least one approval.
2. Confirm CI (pytest) is green.
3. Use "Squash and merge" to keep history tidy.
4. Delete the feature branch locally and on GitHub:
   ```bash
   git checkout main
   git pull origin main
   git branch -d feature/<your-task>
   git push origin --delete feature/<your-task>
   ```

## Fixing Mistakes

- Undo staged files: `git reset HEAD path/to/file`
- Undo last local commit (keeping changes): `git reset --soft HEAD~1`
- Start fresh (dangerous): ask the tech lead before using `git reset --hard`.

## Glossary

- **Branch**: Snapshot of the code where you work safely.
- **Commit**: Saved change with message.
- **Pull request**: Code review request before merging to `main`.

Stick to this playbook and your future self (and teammates) will thank you!
