# Milestone 4 — Windows release pipeline

Historical checkpoint. See [Milestone 5](MILESTONE_5.md) for the browser verification tooling.

Implemented a GitHub Actions workflow for a Windows runner. It enables real loopback and Tk smoke tests, runs the extension checks, builds the portable executable and Inno Setup installer, launches the packaged app with temporary session data, performs a silent install into a temporary directory, verifies the installed app, and uninstalls it. Successful runs upload the Windows packages and smoke reports.

The packaged `--smoke-report PATH` mode verifies bundled assets, foreground hook availability, session start, break suspension and summary storage. It never uses real student data. The package verification script is intended for a disposable build runner.

Foreground monitoring now gates executable-name reads to active focus sessions and releases the WinEvent hook on shutdown. Win32 callback/message signatures are explicit. Simulated Win32 tests cover inactive gating, active events, registration failure and cleanup.

Verified here: 38 Python tests pass; real loopback and Windows GUI tests are skipped. Four extension tests pass, and Python syntax checks pass. Windows workflow, PowerShell scripts, installer and packaged app have not run in this Linux workspace. No Windows binaries are available yet.

To produce and test Windows artifacts, make this PalPal folder the root of a GitHub repository and run the Windows build and smoke tests workflow. This workflow has only been written locally; nothing has been pushed or published.

Still needed for release: successful Windows pipeline results, manual Chrome/Edge interaction checks, resource measurements, and transparent approved character sprites. The current avatar uses source-sheet panels with subtle movement.
