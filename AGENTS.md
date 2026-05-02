# Repository Guidelines

## Project Structure & Module Organization
The application lives under `src/app`. Keep domain math in `src/app/simulation`, request orchestration in `src/app/services`, FastAPI routers in `src/app/api/routers`, and Dash UI code in `src/app/ui`. Shared settings and logging belong in `src/app/infrastructure`.

Runtime data is stored outside the package: `config/defaults.yaml` holds default settings, `data/scenarios/presets.json` stores scenario presets, and `deploy/run-local.ps1` starts the app locally. Tests are split by scope in `tests/unit`, `tests/integration`, and `tests/scenario`. Project notes and architecture material live in `docs/`.

## Build, Test, and Development Commands
Set up a virtual environment and install dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Run the API and dashboard locally:

```powershell
.\deploy\run-local.ps1
```

Or run directly:

```powershell
python -m uvicorn app.main:app --app-dir src --reload
```

Run all tests with `pytest`. Use `pytest tests/unit` for formula changes and `pytest tests/integration` when updating endpoints or wiring.

## Coding Style & Naming Conventions
Follow the existing Python style: 4-space indentation, type hints on public functions, `snake_case` for modules/functions/variables, and `PascalCase` for classes such as Pydantic models. Keep functions focused and place new business rules in `simulation` or `services`, not inside routers or Dash callbacks.

No formatter or linter is configured in `pyproject.toml`, so match the surrounding code closely and keep imports grouped cleanly.

## Testing Guidelines
Use `pytest` for all test types. Name files `test_*.py` and keep test names behavior-oriented, for example `test_run_simulation_endpoint_returns_state_and_trend`. Add or update unit tests for equation changes, integration tests for API contracts, and scenario tests when preset behavior changes.

## Commit & Pull Request Guidelines
Git history is not available in this workspace, so no repository-specific commit convention can be inferred. Use short imperative commit subjects such as `Add filter pressure validation`.

PRs should include a brief summary, affected modules, test evidence, and screenshots when UI behavior under `src/app/ui` changes. Link the related task or issue when one exists.

## Configuration & Data Notes
Treat `config/defaults.yaml` and `data/scenarios/presets.json` as source-controlled inputs. Document new settings in `config/README.md`, and keep scenario IDs stable unless you also update tests and API consumers.
