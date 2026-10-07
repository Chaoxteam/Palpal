# PalPal product constraints

Windows-first, local-first study buddy for children and teens. Loop: set goal, work, receive minimal activity events, classify STUDY/DISTRACTION/UNSURE, wait a configurable grace period, ask gently, return to work. Silence beats unnecessary encouragement.

Hard requirements: no LLM, cloud backend, screen recording, screenshots, typed-content inspection, keylogging, browsing-history storage, shame or punishment. Use the approved cat. Age profiles 6–9, 10–12 and 13+ change tone only. YouTube classification uses goal/title relevance, never a blanket ban. Unknown content stays UNSURE. Confirmations expire with the session. Breaks suspend monitoring. Prompts require cooldowns and caps.

Architecture: desktop, local Chrome/Edge MV3 extension, reusable rules engine, SQLite summary data. Store goal, session timing, break duration, redirects and completion, not browsing content. No account or network service required. Parent features later concern broad progress, never detailed content. First milestone proves the complete algebra → unrelated video → delayed question → No → return flow. Later milestones cover foreground detection, animation, full communication engine, SQLite, settings, performance and installer.
