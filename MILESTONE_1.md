# Milestone 1 status

Historical checkpoint. See [Milestone 2](MILESTONE_2.md) for the current implementation and test status.

Implemented: desktop shell; approved-sheet viewports for idle, talking and break; draggable companion; focus goal/duration/age controls; deterministic rules; Chrome/Edge extension; authenticated local bridge; Windows event-driven foreground executable detection; configurable grace/cooldown/prompt cap; session-only study confirmations; breaks; SQLite summaries; and last-goal restoration.

Privacy safeguards: extension checks active-focus status before accessing title/URL; desktop validates foreground browser, session token, freshness and payload limits; bounded queues reject overload; requests have read timeouts; breaks and new sessions invalidate older tokens. No title/domain logging or persistence. These are implemented safeguards, not an independent security audit.

Verified in Linux: 17 tests pass, including actual HTTP handler parsing via in-memory connections, authentication, inactive/break rejection, foreground rejection, stale tokens/timestamps, malformed data, overload, SQLite persistence, settings validation and focus rules. One live loopback test is opt-in because this workspace prohibits sockets. Python compilation and extension JavaScript syntax pass.

Windows UI, WinEvent hook and real browser integration are unverified. In particular, test rapid switching between browsers and windows, event ordering, inaccessible processes and focus changes during HTTP requests. The extension needs the focused browser to emit an event after a session begins or break ends; returning to the browser normally does this.

Remaining before production:
- Transparent animated sprites and full visual state handling. Viewports preserve source art but include its panel backgrounds.
- Full nonrepeating age-specific library and rolling repeated-distraction window. Prototype suggests reset on the third prompt.
- Scheduled break choices, explicit next-round consent, progress notes, and user-confirmed goal completion. Focus block completion is distinct from goal completion.
- Settings UI, known application lists, history deletion UI, JSONL import and broader subject/domain data. Existing JSONL files are preserved; new sessions use SQLite.
- Windows end-to-end tests, resource measurements, packaging and installer. Idle UI wakes every five seconds; active UI twice per second; window/tab activity is event-driven. No measured performance claim.

Parent features, macOS, and AI remain out of scope.
