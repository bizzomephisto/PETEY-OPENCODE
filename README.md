# OpenCode for PETEY

[![PETEY Desktop](https://img.shields.io/badge/PETEY_Desktop-v0.19.0--experimental.1%2B-7f5af0)](https://github.com/bizzomephisto/PETEY-DESKTOP)
[![Release](https://img.shields.io/github/v/release/bizzomephisto/PETEY-OPENCODE)](https://github.com/bizzomephisto/PETEY-OPENCODE/releases/latest)
[![Tests](https://github.com/bizzomephisto/PETEY-OPENCODE/actions/workflows/test.yml/badge.svg)](https://github.com/bizzomephisto/PETEY-OPENCODE/actions/workflows/test.yml)

Connect PETEY Desktop to the [OpenCode](https://opencode.ai/) coding agent. PETEY can start coding tasks, monitor their progress, cancel active runs, and link to files created inside the selected project.

OpenCode's own permission rules remain active. This add-on does not pass `--auto` and does not bypass OpenCode approval settings.

## Features

- Run `opencode run --format json` in a user-selected project folder.
- Choose from the free OpenCode models exposed by the add-on.
- Keep a bounded live output feed and eight recent project folders.
- Run up to two coding agents concurrently.
- Cancel active runs from the PETEY panel.
- Keep the latest 50 run summaries in private add-on data.
- Expose separate PETEY control permissions for starting and viewing agent runs.
- Link only to reported files that resolve inside the configured project folder.

## Requirements

- [PETEY Desktop v0.19.0-experimental.1 or newer](https://github.com/bizzomephisto/PETEY-DESKTOP/releases)
- OpenCode 1.18 or newer installed for the same operating-system user
- At least one local project folder OpenCode may access

Verify OpenCode before installing the add-on:

```bash
opencode --version
```

## Install

1. Download `petey-opencode-v0.3.3.zip` from the [latest release](https://github.com/bizzomephisto/PETEY-OPENCODE/releases/latest).
2. Extract the archive. It contains one folder named `petey-opencode`.
3. In PETEY, open **Add-ons** and select **Open add-ons folder**.
4. Copy the complete `petey-opencode` folder into that directory.
5. Return to PETEY, enable **OpenCode**, and restart PETEY.

For a source checkout, copy this repository's contents into a folder named `petey-opencode` under PETEY's add-ons directory.

## Configure

1. Open PETEY's **OpenCode** add-on screen.
2. Choose a project folder.
3. Choose an available model.
4. Select **Save setup**.
5. Open **Allow Petey to control** and enable the OpenCode capabilities for the surfaces you trust.

Start a run from the panel or say:

```text
Petey, use OpenCode to fix the mobile navigation in this project.
```

Ask for authoritative progress with:

```text
What is the OpenCode progress?
```

## Storage and safety

Project history and run summaries are stored under `addon-data/petey-opencode/`, outside this source folder. Output is bounded. Artifact requests are resolved and checked against the configured project root before PETEY serves a file.

The agent runs with the current operating-system user's permissions. Review the selected project and OpenCode's permission configuration before starting a task.

## Development

The manifest targets PETEY add-on API version `1`. To run the tests beside a PETEY Desktop checkout:

```bash
PYTHONPATH=/path/to/PETEY-DESKTOP python -m unittest discover -s tests -v
```

See PETEY's [add-on authoring contract](https://github.com/bizzomephisto/PETEY-DESKTOP/blob/main/docs/addons.md) for host behavior and security requirements.
