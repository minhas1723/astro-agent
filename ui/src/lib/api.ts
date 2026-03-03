/**
 * API Configuration - auto-detects same-origin in production,
 * falls back to local dev server via env vars.
 */

const isProduction = typeof window !== "undefined" && window.location.hostname !== "localhost";

const getEnv = (key: string, fallback: string): string => {
  try {
    // @ts-ignore
    return import.meta.env?.[key] || fallback;
  } catch {
    return fallback;
  }
};

export const API_CONFIG = isProduction
  ? {
      // Production: same origin, relative paths
      BASE_URL: "/api/v1",
      WS_URL: `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}/api/v1/chat/ws`,
    }
  : {
      // Development: env vars or local defaults
      BASE_URL: getEnv("VITE_API_URL", "http://localhost:4219/api/v1"),
      WS_URL: getEnv("VITE_WS_URL", "ws://localhost:4219/api/v1/chat/ws"),
    };
