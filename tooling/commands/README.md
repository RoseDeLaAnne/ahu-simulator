# Windows Command Launchers

This folder contains click-to-run Windows launchers that were moved out of the repository root.

Structure:
- `windows/` - `.cmd` files for local dashboard, desktop mode, mobile backend, and Android debug workflows.

Notes:
- Launchers resolve the project root automatically from their current location.
- Root-level `start.bat` remains the primary quick-start entrypoint and delegates to `windows/run-dashboard.cmd`.
