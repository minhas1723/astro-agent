import React, { createContext, useContext, useState, useCallback, useEffect } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
export type UserProfile = {
  name: string;
  email: string;
  dob: string;          // ISO date string  e.g. "1995-11-04"
  birthTime: string;    // "HH:mm" or "" if unknown
  birthPlace: string;
};

export type BirthChart = {
  sun_sign: string;
  moon_sign: string;
  nakshatra: string;
  birth_number: number;
  destiny_number: number;
  planetary_positions: Record<string, string>;  // planet → sidereal sign
  conjunctions: { planets: string[]; sign: string }[];
};

type UserState = {
  profile: UserProfile | null;
  chart: BirthChart | null;
  isOnboarded: boolean;
};

type UserContextType = UserState & {
  /** Save profile + chart after successful API call */
  setSession: (profile: UserProfile, chart: BirthChart) => void;
  /** Clear session (logout) */
  logout: () => void;
};

// ---------------------------------------------------------------------------
// Storage key
// ---------------------------------------------------------------------------
const STORAGE_KEY = "astro_user_session";

function loadSession(): UserState {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw);
      if (parsed?.profile && parsed?.chart) {
        return { profile: parsed.profile, chart: parsed.chart, isOnboarded: true };
      }
    }
  } catch {
    // corrupted data — ignore
  }
  return { profile: null, chart: null, isOnboarded: false };
}

function saveSession(profile: UserProfile, chart: BirthChart) {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ profile, chart }));
}

function clearSession() {
  sessionStorage.removeItem(STORAGE_KEY);
}

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------
const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = useState<UserState>(loadSession);

  // Re-check storage on mount (covers HMR / multi-tab edge cases)
  useEffect(() => {
    setState(loadSession());
  }, []);

  const setSession = useCallback((profile: UserProfile, chart: BirthChart) => {
    saveSession(profile, chart);
    setState({ profile, chart, isOnboarded: true });
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setState({ profile: null, chart: null, isOnboarded: false });
  }, []);

  return (
    <UserContext.Provider value={{ ...state, setSession, logout }}>
      {children}
    </UserContext.Provider>
  );
}

export function useUser() {
  const ctx = useContext(UserContext);
  if (!ctx) throw new Error("useUser must be used within a UserProvider");
  return ctx;
}
