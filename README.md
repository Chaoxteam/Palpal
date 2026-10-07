# PalPal — Windows MVP development build

Local Windows study companion using Python/Tk, deterministic rules, and Chrome/Edge MV3.

## Windows setup

Install Python 3.12+ with Tk support, then from this directory:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m desktop.app
```

Open `chrome://extensions` or `edge://extensions`, enable Developer mode, and Load unpacked `extension/`. In extension options paste the token from PalPal’s Browser pairing token dialog.

Start “Study algebra” for 25 minutes. Visit algebra material, then “Funniest Minecraft Moments” on YouTube. After 20 seconds the cat asks “Study-related?”. Choose No, then return to algebra. Study confirmations expire at session end.

The supplied character sheet is preserved; canvas viewports display the cat’s idle, talking and break panels without recreating the character. Drag the cat canvas to move it.

Only current browser title/domain are used in memory. No cloud, AI, screenshots, keylogging, or browsing history storage. Summaries and settings live under `%LOCALAPPDATA%\PalPal`; session summaries use SQLite. Use Settings to configure grace periods, cooldowns, prompt caps and the recent-intervention window. Changes apply to the next session. The local bridge is token-protected at `127.0.0.1:47831`.

Run tests: `py -m unittest discover -s tests -v`.

See [Milestone 5](docs/MILESTONE_5.md) for current status and [Windows release checks](docs/WINDOWS_RELEASE_CHECKS.md) for build and verification instructions.

## Windows checks

The ordinary suite tests HTTP parsing through in-memory connections. To additionally verify real local sockets on Windows:

```powershell
$env:PALPAL_LIVE_TESTS="1"
py -m unittest discover -s tests -v
```

Run the application and check: switching away from an unrelated video cancels its pending prompt; returning starts a fresh grace period; break and inactive sessions send no browser content; stopping and reopening restores the most recent goal. Windows foreground APIs, appearance and CPU/RAM usage still require a Windows machine.

Previous `sessions.jsonl` files are retained but not imported automatically. New summaries use `sessions.sqlite3`.

## Progress and breaks

Breaks wait for explicit Continue, with one near-end reminder. Stop and save lets the student record a next-step note and confirm whether the goal is complete. Session history shows local summaries, can reuse a goal, and can delete saved summaries. Focus minutes mean time in a focus block excluding breaks; they are not a concentration score.

Build scripts and an installer definition are included, but a Windows executable/installer has not yet been built or tested. The cat still uses approved-sheet state panels, not transparent animation sprites.

## Automated integration checks

```powershell
py -m unittest discover -s tests -v
node tests/extension.test.cjs
```

The desktop integration suite uses real application/session/storage methods with simulated widgets and an in-memory HTTP connection. The extension suite runs the actual worker with simulated Chrome/Edge APIs. These tests complement the Windows acceptance checks; they do not replace them.

## Windows build pipeline

The repository includes `.github/workflows/windows.yml`. On a Windows runner it builds and verifies the executable and installer, then uploads the packages and JSON smoke reports. Place the contents of this PalPal folder at the repository root. Run the workflow manually or through its configured branch/PR triggers. It has not been executed from this workspace.

For local Windows GUI tests, enable `PALPAL_GUI_TESTS=1` alongside `PALPAL_LIVE_TESTS=1`. Installer verification is designed for a disposable build runner.

The Windows workflow also runs a real extension/desktop browser smoke test against synthetic routed pages, then uploads verification reports even on failure. It requires Playwright Chromium and a Windows foreground session. It has not run in this Linux workspace.
