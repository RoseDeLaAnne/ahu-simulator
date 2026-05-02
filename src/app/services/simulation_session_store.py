from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from app.infrastructure.runtime_paths import RuntimePathResolver
from app.simulation.state import SimulationResult, SimulationSession


SIMULATION_SESSION_STORE_SCHEMA_VERSION = 1


class StoredSimulationSession(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = SIMULATION_SESSION_STORE_SCHEMA_VERSION
    session: SimulationSession
    seed_result: SimulationResult


class SimulationSessionStore:
    def __init__(
        self,
        project_root: Path,
        path_resolver: RuntimePathResolver | None = None,
    ) -> None:
        self._path_resolver = path_resolver or RuntimePathResolver(project_root)
        self._file_path = (
            self._path_resolver.runtime_directories.root / "simulation-session.json"
        )

    @property
    def file_path(self) -> Path:
        return self._file_path

    def load(self) -> StoredSimulationSession | None:
        if not self._file_path.exists():
            return None

        try:
            stored = StoredSimulationSession.model_validate_json(
                self._file_path.read_text(encoding="utf-8")
            )
            if stored.schema_version != SIMULATION_SESSION_STORE_SCHEMA_VERSION:
                raise ValueError("Unsupported simulation session schema version")
        except (OSError, ValueError, ValidationError):
            self.clear()
            return None

        return stored

    def save(
        self,
        session: SimulationSession,
        seed_result: SimulationResult,
    ) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        payload = StoredSimulationSession(session=session, seed_result=seed_result)
        temporary_path = self._file_path.with_suffix(".tmp")
        temporary_path.write_text(payload.model_dump_json(indent=2), encoding="utf-8")
        temporary_path.replace(self._file_path)

    def clear(self) -> None:
        try:
            self._file_path.unlink(missing_ok=True)
        except OSError:
            pass
