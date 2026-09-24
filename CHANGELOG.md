# Changelog

## v0.3.7 — 2026-09-23

- Keep interactive HTML games working inside PETEY's isolated artifact preview.
- Provide preview-only in-memory `localStorage` and `sessionStorage` without exposing PETEY's origin.

## v0.3.6 — 2026-09-23

- Add an optional compact OpenCode activity badge to PETEY's desktop text-chat header.
- Show the live running-job count and open the OpenCode panel when the badge is clicked.

## v0.3.5 — 2026-09-23

- Add a setting for unattended runs to continue through OpenCode's `doom_loop` recovery prompt.
- Keep broad `--auto` approval disabled and preserve all other OpenCode permission rules.

## v0.3.4 — 2026-09-23

- Open generated web artifacts in PETEY's sandboxed preview instead of replacing the app.
- Add Close and Open in browser controls through the PETEY host viewer.

## v0.3.3 — 2026-09-22

- Load the current model catalog from the installed OpenCode CLI.
- Add a responsive Refresh models control with a bundled offline fallback.

## v0.3.2 — 2026-09-22

- Replace the retired MiMo 2.5 free model with MiMo 2.6 Flash.
- Automatically migrate existing MiMo 2.5 selections and improve OpenCode error messages.

## v0.3.1 — 2026-09-22

- Start, monitor, and cancel OpenCode coding-agent runs.
- Track bounded JSON event output and recent run summaries.
- Detect created project files and expose relative PETEY artifact links.
- Announce completed runs without reading file names aloud in speech.
- Keep OpenCode's native permission system active.
