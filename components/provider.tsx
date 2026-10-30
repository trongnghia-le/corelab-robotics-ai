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
type Context = {
  state: AppState | null;
  error: string;
  busy: boolean;
  refresh: () => Promise<void>;
  act: (action: unknown) => Promise<unknown>;
  notify: (message: string) => void;
};
const Context = createContext<Context | null>(null);
export function Provider({ children }: { children: ReactNode }) {
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
      setError(e instanceof Error ? e.message : "Không thể đọc dữ liệu.");
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
        setToast(e instanceof Error ? e.message : "Không thể lưu dữ liệu.");
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
  return (
    <div className="empty-state" role={error ? "alert" : "status"}>
      <h2>{error ? "Không thể mở workspace" : "Đang mở workspace…"}</h2>
      <p>{error || "Đọc dữ liệu cục bộ."}</p>
      {error && (
        <button onClick={() => void refresh().catch(() => {})}>Thử lại</button>
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
    "Clipboard chưa sẵn sàng. Hãy chọn và sao chép nội dung bên dưới.",
  );
}
