import fs from "node:fs";
import path from "node:path";
import type { CapacitorConfig } from "@capacitor/cli";

const PLACEHOLDER_HOSTNAMES = new Set([
  "api.ahu-simulator.example",
  "ahu-simulator.example",
  "example.com",
  "www.example.com",
  "example.net",
  "www.example.net",
  "example.org",
  "www.example.org",
]);

const RESERVED_HOSTNAME_SUFFIXES = [".example", ".invalid", ".test", ".localhost"];

function loadLocalEnvFile(): void {
  const envPath = path.resolve(__dirname, ".env");
  if (!fs.existsSync(envPath)) {
    return;
  }

  const content = fs.readFileSync(envPath, "utf-8");
  for (const line of content.split(/\r?\n/u)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) {
      continue;
    }

    const separatorIndex = trimmed.indexOf("=");
    if (separatorIndex <= 0) {
      continue;
    }

    const key = trimmed.slice(0, separatorIndex).trim();
    if (!key || process.env[key]?.trim()) {
      continue;
    }

    let value = trimmed.slice(separatorIndex + 1).trim();
    const wrappedInSingleQuotes = value.startsWith("'") && value.endsWith("'");
    const wrappedInDoubleQuotes = value.startsWith('"') && value.endsWith('"');
    if ((wrappedInSingleQuotes || wrappedInDoubleQuotes) && value.length >= 2) {
      value = value.slice(1, -1);
    }

    process.env[key] = value;
  }
}

function failConfig(message: string): never {
  throw new Error(`[mobile] ${message}`);
}

function isPlaceholderHostname(hostname: string): boolean {
  const normalizedHostname = hostname.trim().toLowerCase();
  if (!normalizedHostname) {
    return true;
  }

  if (PLACEHOLDER_HOSTNAMES.has(normalizedHostname)) {
    return true;
  }

  return RESERVED_HOSTNAME_SUFFIXES.some((suffix) => {
    const suffixWithoutDot = suffix.slice(1);
    return (
      normalizedHostname === suffixWithoutDot ||
      normalizedHostname.endsWith(suffix)
    );
  });
}

function normalizeBackendDashboardPath(url: URL): URL {
  const normalized = new URL(url.toString());
  const trimmedPath = normalized.pathname.trim().replace(/\/+$/u, "");
  if (!trimmedPath || trimmedPath === "/") {
    normalized.pathname = "/dashboard";
  }
  return normalized;
}

function resolveBackendUrl(rawUrl: string | undefined): URL {
  const normalizedUrl = rawUrl?.trim();
  if (!normalizedUrl) {
    failConfig(
      "MOBILE_BACKEND_HTTPS_URL is required. Create mobile/.env or export it before running Capacitor commands.",
    );
  }

  let parsedUrl: URL;
  try {
    parsedUrl = new URL(normalizedUrl);
  } catch {
    failConfig(`MOBILE_BACKEND_HTTPS_URL is not a valid URL: ${normalizedUrl}`);
  }

  if (parsedUrl.protocol !== "https:") {
    failConfig("MOBILE_BACKEND_HTTPS_URL must use HTTPS.");
  }

  if (isPlaceholderHostname(parsedUrl.hostname)) {
    failConfig(
      "MOBILE_BACKEND_HTTPS_URL points to a placeholder/reserved domain. Set a real backend host.",
    );
  }

  return normalizeBackendDashboardPath(parsedUrl);
}

loadLocalEnvFile();

const parsedBackendUrl = resolveBackendUrl(process.env.MOBILE_BACKEND_HTTPS_URL);
const resolvedBackendUrl = parsedBackendUrl.toString();
const releaseType =
  process.env.MOBILE_ANDROID_RELEASE_TYPE?.toUpperCase() === "APK" ? "APK" : "AAB";

const config: CapacitorConfig = {
  appId: process.env.MOBILE_APP_ID?.trim() || "com.ahusimulator.mobile",
  appName: process.env.MOBILE_APP_NAME?.trim() || "AHU Simulator",
  webDir: "web",
  android: {
    path: "android",
    buildOptions: {
      releaseType,
      keystorePath: process.env.MOBILE_ANDROID_KEYSTORE_PATH,
      keystorePassword: process.env.MOBILE_ANDROID_KEYSTORE_PASSWORD,
      keystoreAlias: process.env.MOBILE_ANDROID_KEY_ALIAS,
      keystoreAliasPassword: process.env.MOBILE_ANDROID_KEY_ALIAS_PASSWORD,
    },
  },
  server: {
    url: resolvedBackendUrl,
    androidScheme: "https",
    cleartext: false,
    allowNavigation: [parsedBackendUrl.origin],
    errorPath: `unavailable.html?backend=${encodeURIComponent(resolvedBackendUrl)}`,
  },
};

export default config;
