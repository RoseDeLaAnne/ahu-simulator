# Logs Artifact Area

Purpose:
- Store local runtime and troubleshooting logs outside repository root.

Recommended structure:
- `local/YYYY-MM-DD/`
- `mobile/YYYY-MM-DD/`
- `tunnel/YYYY-MM-DD/`

Rules:
- Runtime code must not rely on fixed filenames here.
- Keep this folder for diagnostics only.
