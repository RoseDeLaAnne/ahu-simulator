# Windows EXE Smoke Checklist

Date baseline: 2026-04-18.

## 1) Build and launch

1. Build bundle: `./deploy/build-windows-exe.ps1 -Clean`.
2. Verify executable exists: `dist/windows-exe/AhuSimulator/AhuSimulator.exe`.
3. Launch `AhuSimulator.exe`.
4. Confirm native app window opens and loads `http://127.0.0.1:<auto-port>/dashboard` inside the window.
5. Fallback check: set `AHU_SIMULATOR_DESKTOP_APP_MODE=0` and confirm browser mode still works.

## 2) API smoke

1. Open `http://127.0.0.1:<auto-port>/health` -> status 200.
2. Open `http://127.0.0.1:<auto-port>/docs`.
3. Check `GET /scenarios` and `POST /simulation/run` from Swagger UI.

## 3) Runtime-dir validation

1. Confirm runtime root exists: `%LOCALAPPDATA%/AhuSimulator`.
2. Trigger scenario archive save in dashboard and verify file in `%LOCALAPPDATA%/AhuSimulator/scenario-archive/<date>/`.
3. Trigger export build and verify files in `%LOCALAPPDATA%/AhuSimulator/exports/<date>/`.
4. Trigger event creation (run scenario or export) and verify JSON in `%LOCALAPPDATA%/AhuSimulator/event-log/<date>/`.
5. Trigger demo bundle build and verify zip + manifest in `%LOCALAPPDATA%/AhuSimulator/demo-packages/<date>/`.

## 4) UX sanity

1. Check dashboard loads CSS/JS assets correctly.
2. Ensure navigation tabs and graphs render without console errors.
3. Ensure app keeps running when dashboard tab is refreshed.

## 5) Exit and restart

1. Close app process.
2. Launch again.
3. Verify previous runtime artifacts remain available in `%LOCALAPPDATA%/AhuSimulator`.
