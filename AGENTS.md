# OpenCode for PETEY coding-agent context

Scope: this repository. Current add-on version: 0.4.0; PETEY add-on API: 1.
Read PETEY Desktop's `ADDONS.md` and `docs/addons.md` before changing host contracts.

## Product boundary

This add-on launches the user's installed OpenCode CLI inside one explicitly selected
project, tracks at most two concurrent runs, and exposes bounded status/artifact links.
OpenCode's own permission configuration remains authoritative. PETEY does not pass
`--auto`; the optional repeated-tool continuation answers only OpenCode's documented
`doom_loop` recovery prompt.

## Architecture and data flow

- `petey-addon.json` declares ID `petey-opencode`, API 1, and the panel assets.
- `addon.py` composes `OpenCodeBridge`, registers namespaced panel APIs, validates
  same-origin mutations, and returns the bridge for tools and shutdown.
- `opencode_bridge.py:OpenCodeBridge` owns private configuration, model choices,
  subprocesses, output readers, recent-run archives, cancellation, and tool specs.
- `start()` builds a fixed argv for `opencode run --format json`, uses the selected
  project as `cwd`, enforces the two-run ceiling, and starts bounded collectors.
- Run state and output are synchronized. `_archive()` retains only the latest 50
  summaries under the add-on data directory.
- `artifact()` accepts only reported paths that resolve inside the configured project.
  PETEY handles preview and external-browser presentation; never emit arbitrary paths.
- `tool_specs()` separates `start_agent_run` from `view_agent_runs`, uses explicit
  intent gates, and makes status authoritative for completion claims.
- `panel.js` owns setup, run polling, cancel controls, bounded live output, recent
  project selection, and the optional Command Center activity indicator.

## Preserve these contracts

- Never bypass OpenCode permission rules, synthesize broad approval flags, or run a
  shell command assembled from user text. Use argv arrays and a fixed executable.
- Project folders must exist and be directories. All artifact links must remain
  descendant paths after canonical resolution, including symlink handling.
- Bound prompt length, output retained per run, process count, recent runs, and API
  response sizes. Cancellation and `close()` must terminate direct children once.
- Do not claim a run completed from UI timing or model prose. Read the run snapshot.
- Keep start and view capabilities independently gated by PETEY control policy.
- Hidden/control UI strings enter the DOM through safe text APIs. Artifact HTML runs
  only inside PETEY's sandboxed preview contract.
- Config and run metadata belong in `context.data_dir`; never write runtime state to
  the installed source directory.

## Task map

| Task | Primary anchors |
| --- | --- |
| Configuration/models | `opencode_bridge.py` load/save/config methods |
| Process lifecycle | `start`, collectors, `cancel`, `close` |
| Status/history | `get`, `recent_runs`, `_archive` |
| Artifact safety | `artifact` and related path normalization |
| Model tools | `tool_specs` intent/required/control gates |
| HTTP composition | `addon.py:setup` |
| Panel/activity badge | `panel.js`, `panel.html`, `panel.css` |
| Tests | `tests/test_bridge.py`, `tests/test_activity_indicator.py` |

## Validation

```bash
PYTHONPATH=/path/to/PETEY-DESKTOP python -m unittest discover -s tests -v
python -m py_compile addon.py opencode_bridge.py
python -m json.tool petey-addon.json >/dev/null
node --check panel.js
```

Unit tests must fake OpenCode and never launch a real agent. After lifecycle or panel
changes, smoke-test one run, cancellation, artifact preview, and shutdown with a
disposable project before release.
