"use client";
// Light/dark switch. The server renders <html data-theme> from a cookie, so
// the first paint is already right; localStorage keeps the choice and syncs
// other CoreLab windows (the study desk) through the storage event.
import { useEffect, useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";
import { useI18n } from "@/lib/i18n";
import {
  THEME_COOKIE,
  THEME_STORAGE,
  parseTheme,
  type Theme,
} from "@/lib/theme";

const EVENT = "corelab-theme";

function read(): Theme {
  return parseTheme(document.documentElement.dataset.theme);
}

function apply(theme: Theme, persist = true) {
  document.documentElement.dataset.theme = theme;
  document.cookie = `${THEME_COOKIE}=${theme}; path=/; max-age=31536000; SameSite=Lax`;
  if (persist)
    try {
      localStorage.setItem(THEME_STORAGE, theme);
    } catch {
      // Storage blocked: the cookie still keeps the choice.
    }
  window.dispatchEvent(new Event(EVENT));
}

function subscribe(listener: () => void) {
  const onStorage = (e: StorageEvent) => {
    if (e.key === THEME_STORAGE && e.newValue)
      apply(parseTheme(e.newValue), false);
  };
  window.addEventListener(EVENT, listener);
  window.addEventListener("storage", onStorage);
  return () => {
    window.removeEventListener(EVENT, listener);
    window.removeEventListener("storage", onStorage);
  };
}

/** Current theme, re-rendering on changes (also from other windows). */
export function useTheme(initial: Theme = "dark") {
  return useSyncExternalStore(subscribe, read, () => initial);
}

export function ThemeToggle() {
  const { tx } = useI18n();
  const theme = useTheme();
  useEffect(() => {
    // localStorage is the source of truth; repair a missing or stale cookie.
    try {
      const stored = localStorage.getItem(THEME_STORAGE);
      if (stored && parseTheme(stored) !== read()) apply(parseTheme(stored));
    } catch {
      // Ignore blocked storage.
    }
  }, []);
  const next = theme === "dark" ? "light" : "dark";
  const label =
    next === "light"
      ? tx("Switch to light theme", "Chuyển sang giao diện sáng")
      : tx("Switch to dark theme", "Chuyển sang giao diện tối");
  return (
    <button
      type="button"
      className="icon-button theme-toggle"
      aria-label={label}
      title={label}
      onClick={() => apply(next)}
    >
      {theme === "dark" ? <Sun size={17} /> : <Moon size={17} />}
    </button>
  );
}
