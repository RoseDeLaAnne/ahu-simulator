# Release Clean-Install Checklist

Date baseline: 2026-04-18.

## 1) Pre-release gate

1. Confirm project version in `pyproject.toml` (`[project].version`).
2. Confirm release tag format `vMAJOR.MINOR.PATCH`.
3. Confirm CI secrets are configured:
   - `WINDOWS_CODESIGN_CERT_BASE64`, `WINDOWS_CODESIGN_PASSWORD`;
   - `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS`, `ANDROID_KEY_ALIAS_PASSWORD`.
4. Confirm release notes include known limitations for desktop and mobile modes.

## 2) Windows clean-install validation

1. Use a clean Windows 10/11 machine (without local dev environment).
2. Install package produced from `windows-pyinstaller` workflow artifact.
3. Launch app from Start menu or desktop shortcut.
4. Confirm dashboard opens in native app window.
5. Confirm API endpoints respond:
   - `/health` returns status 200;
   - `/docs` loads Swagger.
6. Run one simulation scenario and confirm charts/status cards update.
7. Trigger export and verify files are written to `%LOCALAPPDATA%/AhuSimulator/exports/<date>/`.
8. Trigger archive save and verify files in `%LOCALAPPDATA%/AhuSimulator/scenario-archive/<date>/`.
9. Trigger event-producing action and verify `%LOCALAPPDATA%/AhuSimulator/event-log/<date>/`.
10. Restart app and confirm previous runtime artifacts persist.
11. Verify executable signature in file properties (if signing secrets are configured).

## 3) Android clean-install validation

1. Use a clean Android device (API 24+), remove previous app build.
2. Install release APK from `android-capacitor` workflow artifact.
3. Launch app and confirm dashboard loads from HTTPS backend.
4. Confirm one simulation run completes and trend/KPI blocks refresh.
5. Confirm export action returns successful status in UI.
6. Disable network temporarily and confirm fallback page is shown.
7. Re-enable network and confirm app returns to operational state.
8. Verify app package reports expected `versionName` and `versionCode`.
9. Verify release signing certificate fingerprint if signed build is expected.

## 4) Release evidence pack

1. Attach workflow run URLs for Windows and Android jobs.
2. Attach artifact file names and hashes.
3. Attach screenshots from clean-install validation on both platforms.
4. Record unresolved known issues and mitigations.
