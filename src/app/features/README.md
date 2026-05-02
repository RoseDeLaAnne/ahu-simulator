# Features Package

Each feature owns its runtime orchestration and contracts.

Typical layout:
- `service.py`: orchestration and application flow
- `api.py`: feature router handlers
- `schemas.py`: transport schemas when needed
- `viewmodel.py`: UI projection when needed

Migration policy:
- move from `app/services` feature by feature
- leave compatibility shims in old paths to keep imports stable
