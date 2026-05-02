# AHU Simulator mobile shell (Capacitor + Android)

This directory contains the Android shell that loads AHU Simulator from a remote HTTPS backend.

## Implemented scope

- Capacitor shell project in `mobile/`;
- configured `capacitor.config.ts` (`appId`, `appName`, Android platform, HTTPS `server.url`);
- debug and release build scripts for APK/AAB;
- fallback screen for backend unavailability (`web/unavailable.html`) with effective backend URL for diagnostics.

## Prerequisites

- Node.js 20+ and npm;
- Java JDK 21+ (`JAVA_HOME` configured);
- Android SDK + Platform Tools (`ANDROID_HOME` or `ANDROID_SDK_ROOT`);
- running HTTPS backend (see [../deploy/mobile-backend/README.md](../deploy/mobile-backend/README.md)).

## Setup

1. Copy [.env.example](.env.example) to `mobile/.env` and update values.
  - `MOBILE_BACKEND_HTTPS_URL` is required and must point to a real HTTPS endpoint.
  - placeholder domains like `*.example` are rejected during build/sync.
2. Install dependencies:

```powershell
cd mobile
npm install
```

3. Optional manual env load in PowerShell session:

```powershell
Get-Content .env | ForEach-Object {
  if ($_ -and -not $_.StartsWith("#")) {
    $pair = $_ -split "=", 2
    Set-Item -Path "Env:$($pair[0])" -Value $pair[1]
  }
}
```

`build-android.ps1` and `capacitor.config.ts` automatically read `mobile/.env`,
so manual export is not required for normal builds.

4. Create native Android project once:

```powershell
npm run add:android
```

5. Sync config/plugins:

```powershell
npm run sync
```

## Build commands

Debug APK:

```powershell
npm run build:debug
```

Debug APK without backend reachability probe (local/offline diagnostics only):

```powershell
npm run build:debug:offline
```

Release APK:

```powershell
npm run build:release:apk
```

Release AAB:

```powershell
npm run build:release:aab
```

Artifacts:

- debug APK: `android/app/build/outputs/apk/debug/app-debug.apk`;
- release APK: `android/app/build/outputs/apk/release/app-release-unsigned.apk`;
- release AAB: `android/app/build/outputs/bundle/release/app-release.aab`.

Before sync/build, script validates backend settings:

- checks `MOBILE_BACKEND_HTTPS_URL` exists and uses HTTPS;
- rejects placeholder hostnames (`*.example`);
- probes `<backend-origin>/health` (unless `-SkipBackendProbe` is used).

## Versioning

`mobile/scripts/build-android.ps1` resolves version from
`../pyproject.toml` (`[project].version`) via
`../deploy/resolve-release-version.ps1` and exports:

- `AHU_ANDROID_VERSION_NAME`;
- `AHU_ANDROID_VERSION_CODE`.

`versionCode` is derived as:

`major * 10000 + minor * 100 + patch`

Optional override for CI/manual release builds:

```powershell
$env:AHU_RELEASE_VERSION = "0.2.0"
npm run build:release:aab
```

## Release signing

`mobile/android/app/build.gradle` applies release signing when all
variables are provided:

- `AHU_ANDROID_KEYSTORE_PATH` (или `MOBILE_ANDROID_KEYSTORE_PATH`);
- `AHU_ANDROID_KEYSTORE_PASSWORD` (или `MOBILE_ANDROID_KEYSTORE_PASSWORD`);
- `AHU_ANDROID_KEY_ALIAS` (или `MOBILE_ANDROID_KEY_ALIAS`);
- `AHU_ANDROID_KEY_ALIAS_PASSWORD` (или `MOBILE_ANDROID_KEY_ALIAS_PASSWORD`).

Если значения отсутствуют, release build остается unsigned.

## CI

Android CI workflow:

- `../.github/workflows/android-capacitor.yml`.

Для signed release в GitHub Actions добавьте repository secrets:

- `ANDROID_KEYSTORE_BASE64`;
- `ANDROID_KEYSTORE_PASSWORD`;
- `ANDROID_KEY_ALIAS`;
- `ANDROID_KEY_ALIAS_PASSWORD`.

## Verify on target devices

1. Enable USB debugging on each test phone.
2. Connect devices and run:

```powershell
npm run check:devices
```

3. Install debug APK on connected device:

```powershell
cd android
.\gradlew.bat installDebug
```

4. Smoke-check the flow:
- open app and wait for dashboard load;
- run one scenario and verify trend updates;
- check export action response from UI;
- confirm fallback screen appears if backend is unavailable.

## Notes

- By design this shell uses remote `server.url`, so network and backend availability are mandatory.
- Keep `server.cleartext=false` for production.
- Release APK is unsigned until keystore values are provided.

## Troubleshooting: "Не удается подключиться к серверу"

1. Verify app build uses expected endpoint from `mobile/.env`.
2. Verify `https://<host>/health` returns 200 from phone network.
3. Rebuild and reinstall app (`npm run build:debug`, then `cd android; .\gradlew.bat installDebug`).
4. If diagnostics are needed without live backend, use `npm run build:debug:offline`.

Additional notes:

- Reserved placeholder hosts are now blocked during build (`example.com/.net/.org`, `*.example`, `*.invalid`, `*.test`, `*.localhost`).
- Build now validates both `<backend>/health` and the configured dashboard URL.
- Fallback screen `unavailable.html` now allows manual HTTPS URL override and one-tap retry to open the dashboard.
