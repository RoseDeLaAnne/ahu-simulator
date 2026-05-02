# Domain Package

Place only pure domain logic here:
- equations, invariants, state transitions
- no FastAPI/Dash/CLI imports
- no filesystem or environment adapters

Migration policy:
- move modules from `app/simulation` gradually
- keep import shims until all consumers are switched
