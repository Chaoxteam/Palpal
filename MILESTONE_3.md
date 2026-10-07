# Milestone 3 — integration and reliability

Historical checkpoint. See [Milestone 4](MILESTONE_4.md) for current release tooling.

Completed:
- Classification rules moved out of the session engine into a separate module with local JSON data. Added study/distraction application lists and more subject/domain vocabulary.
- Generic words such as homework, math and video do not alone prove relevance. Relevant topics mixed with unrelated entertainment signals remain UNSURE. Explicit entertainment-related study goals can still match.
- Browser identity is checked again when queued events reach the desktop; a Chrome event cannot become an Edge prompt after a foreground switch.
- Save errors preserve the session for retry instead of closing it. Focus time is capped at the planned duration when completion is detected late.
- Idle cat panel has subtle, low-frequency breathing movement. Noninteractive speech bubbles clear after six seconds; unanswered prompts remain available. The approved sheet remains intact.
- Desktop integration tests exercise actual app methods and actual HTTP parsing through in-memory connections, using fake GUI widgets and a controlled clock. Extension tests execute the service worker against mocked browser APIs.

Verification: 35 Python tests pass; one live-loopback test remains opt-in/skipped. Four JavaScript tests pass. Python syntax checks pass. Tests cover the full algebra → unrelated video → grace → No → study → summary flow, stale answers, switching browsers, break suspension, internal tabs, and save retry. They do not verify Windows OS hooks, real browser permissions, visible GUI rendering or installer behavior.

Release blockers remain: Windows end-to-end and install/uninstall checks; actual idle resource measurements; and transparent approved animation assets. The source sheet panels have backgrounds and are not finished sprite assets. No Windows binary has been produced here.
