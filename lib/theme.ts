export type Theme = "dark" | "light";
export const THEME_COOKIE = "corelab-theme";
export const THEME_STORAGE = "corelab-theme";
export function parseTheme(value: unknown): Theme {
  return value === "light" ? "light" : "dark";
}
