# Windows verification

## Build

Install Python 3.12+ and Inno Setup 6. Put `ISCC.exe` on PATH. From the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File packaging/build.ps1
```

Outputs should be `dist/PalPal/PalPal.exe`, `dist/PalPal-portable.zip`, and, if Inno Setup is available, `dist/PalPal-Setup.exe`. No build output has been produced in Linux. The installer runs per-user without administrator privileges. Browser extensions require manual loading/pairing; they are included in the install's `extension` directory. Uninstall preserves local summaries; delete them through Session history first if desired.

## Acceptance checks

1. Launch packaged PalPal. Check source-sheet cat states, speech bubbles, dragging, screen scaling and startup without an account.
2. Load extension in Chrome and Edge; pair each. Start algebra, visit Khan Academy, then unrelated Minecraft YouTube content. No prompt before configured grace. Choose No and return to algebra.
3. Switch to another program and rapidly alternate Chrome/Edge before grace ends. Old browser prompts must disappear. Internal browser pages must clear previous content.
4. Confirm a title as study; revisit it this session, then a new session. Confirmation must expire at session end.
5. Take a break. No activity prompts during break or while waiting to resume. One reminder near the end. Resume explicitly and verify break time is excluded.
6. Complete a block, record partial progress, and leave goal-complete unchecked. Start a five-minute reset and ten-minute block. Separately confirm goal completion and verify history distinguishes it from timer completion.
7. Save settings, restart, check values. Enter invalid settings and confirm clear errors. Delete summaries and verify history is empty after restarting.
8. Close/reopen and verify most recent goal. Launch a second instance and confirm bridge failure is visible.
9. Install, launch from shortcuts, uninstall, and verify no orphaned PalPal process remains.

## Resource measurement

Install optional tooling with `py -m pip install psutil`. Find PalPal's PID in Task Manager. Run:

```powershell
py tools/measure_resources.py 12345 --seconds 300 --output idle.csv
```

Repeat for active quiet study, tab switches and breaks. Report machine/Windows/browser versions, median and peak CPU, memory and disk deltas. Compare idle against the machine's background baseline. This tool reads counters only; no window content, titles or typed text. Measurements have not yet been collected.

## Automated package verification

The Windows workflow also runs `packaging/verify-package.ps1` on its disposable runner. This checks both portable and installed executables using temporary data, then uninstalls the temporary installation. Reports are uploaded with the packages. These scripts are authored but have not run in this Linux environment.
