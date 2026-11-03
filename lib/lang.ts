export type Lang = "en" | "vi";
export const LANG_COOKIE = "corelab-lang";
export const LANG_STORAGE = "corelab-lang";
export function parseLang(value: unknown): Lang {
  return value === "vi" ? "vi" : "en";
}
