"use client";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import type { AppState } from "@/lib/types";
import { I18nProvider, useI18n } from "@/lib/i18n";
import { topicMap } from "@/lib/curriculum";
import type { Lang } from "@/lib/lang";
type Context = {
  state: AppState | null;
  error: string;
  busy: boolean;
  refresh: () => Promise<void>;
  act: (action: unknown) => Promise<unknown>;
  notify: (message: string) => void;
  /** Topic title; the translated lesson title when Vietnamese is on. */
  title: (id: string) => string;
};
const Context = createContext<Context | null>(null);
export function Provider({
  children,
  lang = "en",
}: {
  children: ReactNode;
  lang?: Lang;
}) {
  return (
    <I18nProvider initial={lang}>
      <CoreProvider>{children}</CoreProvider>
    </I18nProvider>
  );
}
function CoreProvider({ children }: { children: ReactNode }) {
  const { lang } = useI18n();
  const [titles, setTitles] = useState<Record<string, string>>({});
  useEffect(() => {
    if (lang !== "vi") {
      setTitles({});
      return;
    }
    const controller = new AbortController();
    fetch("/api/titles?lang=vi", { signal: controller.signal })
      .then((r) => r.json())
      .then((d) => setTitles(d.titles ?? {}))
      .catch(() => {});
    return () => controller.abort();
  }, [lang]);
  const title = useCallback(
    (id: string) => titles[id] ?? topicMap[id]?.title ?? id,
    [titles],
  );
  const [state, setState] = useState<AppState | null>(null),
    [error, setError] = useState(""),
    [pending, setPending] = useState(0),
    [toast, setToast] = useState("");
  const refresh = useCallback(async () => {
    try {
      const r = await fetch("/api/state", { cache: "no-store" });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error);
      setState(data);
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to read data.");
      throw e;
    }
  }, []);
  useEffect(() => {
    void refresh().catch(() => {});
  }, [refresh]);
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(""), 5000);
    return () => clearTimeout(timer);
  }, [toast]);
  const act = useCallback(
    async (action: unknown) => {
      setPending((n) => n + 1);
      try {
        const r = await fetch("/api/action", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(action),
        });
        const data = await r.json();
        if (!r.ok) throw new Error(data.error);
        await refresh();
        return data;
      } catch (e) {
        setToast(e instanceof Error ? e.message : "Unable to save data.");
        throw e;
      } finally {
        setPending((n) => n - 1);
      }
    },
    [refresh],
  );
  return (
    <Context.Provider
      value={{
        state,
        error,
        busy: pending > 0,
        refresh,
        act,
        notify: setToast,
        title,
      }}
    >
      {children}
      <div className="toast-region" role="status" aria-live="polite">
        {toast && <div className="toast">{toast}</div>}
      </div>
    </Context.Provider>
  );
}
export function useCore() {
  const c = useContext(Context);
  if (!c) throw new Error("Missing CoreLab provider");
  return c;
}
export function Loading() {
  const { error, refresh } = useCore();
  const { tx } = useI18n();
  return (
    <div className="empty-state" role={error ? "alert" : "status"}>
      <h2>
        {error
          ? tx("Unable to open workspace", "Không mở được không gian học")
          : tx("Opening workspace…", "Đang mở không gian học…")}
      </h2>
      <p>{error || tx("Reading local data.", "Đang đọc dữ liệu cục bộ.")}</p>
      {error && (
        <button onClick={() => void refresh().catch(() => {})}>
          {tx("Try again", "Thử lại")}
        </button>
      )}
    </div>
  );
}
export async function copyText(value: string) {
  if (navigator.clipboard) {
    await navigator.clipboard.writeText(value);
    return;
  }
  throw new Error(
    "Clipboard is unavailable. Select and copy the content below.",
  );
}
