# Milestone 2 — communication, progress and release tooling

Historical checkpoint. See [Milestone 3](MILESTONE_3.md) for current status.

Implemented:
- Prewritten age-specific messages in `data/messages.json`, immediate repeat avoidance and optional silence after a recent return message.
- Reset suggestions based on a rolling recent-prompt window. Keep going does not accidentally mark content as study-related.
- One near-end break reminder. Break completion waits for explicit Continue; waiting time remains excluded from focus-block time.
- A completed focus block offers a five-minute reset followed by a ten-minute block.
- Progress notes and explicit student-confirmed goal completion, independent of timer completion. Saving progress disables monitoring and freezes elapsed time.
- Settings UI with validation and atomic local saves; values apply to the next session.
- SQLite schema upgrades, recent summary history, reuse of selected goals, and deletion of all summaries including legacy JSONL files.
- Browser identity validation and empty-context events for internal browser pages. Stale prompts are cleared on context changes.
- Windows portable-build script, Inno Setup installer definition and a metrics-only resource measurement tool.

Verification: 26 tests pass and one opt-in live loopback test is skipped. Python syntax and JavaScript syntax checks pass. Socket restrictions prevent the live loopback test here. Tk and Pillow import, but this environment has no display server for interactive UI verification.

Remaining release work: Windows UI/browser/foreground tests, compiling and installing/uninstalling the Windows package, CPU/RAM/disk measurements, and transparent approved animation assets. Current avatar states use viewports of the supplied sheet; this is not a finished animated desktop pet. Known domain/subject lists remain small. No production-ready or performance claim is made.

Focus minutes measure elapsed time in an active focus block, excluding breaks and waiting to resume. They do not claim to measure a child's concentration. No raw activity is stored.
