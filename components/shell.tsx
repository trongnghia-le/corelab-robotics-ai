"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState, type ReactNode } from "react";
import {
  Atom,
  LayoutDashboard,
  Network,
  BookOpen,
  ClipboardCheck,
  FlaskConical,
  Route,
  MessageSquare,
  Settings,
  Library,
  PanelLeftClose,
  Menu,
  ArrowUpRight,
  Languages,
  PanelRight,
  PanelLeftOpen,
} from "lucide-react";
import { useI18n, type Dict } from "@/lib/i18n";
import { ThemeToggle } from "./theme-toggle";
import { DeskPanel, useDeskPanel } from "./desk-panel";
type TKey = keyof Dict;
/** Open (or focus) the study desk as its own window beside the lesson. */
export function openDesk() {
  const width = Math.min(760, Math.round(screen.availWidth * 0.42));
  const left = screen.availWidth - width;
  window
    .open(
      "/desk",
      "corelab-desk",
      `popup,width=${width},height=${screen.availHeight},left=${left},top=0`,
    )
    ?.focus();
}
const main = [
  ["/", "nav.dashboard", LayoutDashboard],
  ["/roadmap", "nav.roadmap", Network],
  ["/lessons", "nav.lessons", BookOpen],
  ["/practice", "nav.practice", FlaskConical],
  ["/assessments", "nav.review", ClipboardCheck],
] as const;
const extra = [
  ["/paths", "nav.paths", Route],
  ["/tutor", "nav.tutor", MessageSquare],
  ["/sources", "nav.sources", Library],
] as const;
const labels: Record<string, TKey> = {
  objectives: "nav.lab",
  roadmap: "nav.roadmap",
  lessons: "nav.lessons",
  assessments: "nav.review",
  paths: "nav.paths",
  practice: "nav.practice",
  tutor: "nav.tutor",
  settings: "nav.settings",
  sources: "nav.sources",
};
export function Shell({
  children,
  v2Enabled = false,
}: {
  children: ReactNode;
  v2Enabled?: boolean;
}) {
  const pathname = usePathname(),
    { t, lang, setLang } = useI18n(),
    [open, setOpen] = useState(false);
  const desk = useDeskPanel();
  // Wide screens can fold the sidebar into an icon rail; remembered per browser.
  const [collapsed, setCollapsed] = useState(false);
  useEffect(() => {
    try {
      setCollapsed(localStorage.getItem("corelab:sidebar") === "rail");
    } catch {}
  }, []);
  function toggleRail() {
    setCollapsed((c) => {
      try {
        localStorage.setItem("corelab:sidebar", c ? "full" : "rail");
      } catch {}
      return !c;
    });
  }
  const closeRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLButtonElement>(null);
  const wasOpen = useRef(false);
  useEffect(() => {
    if (open) closeRef.current?.focus();
    else if (wasOpen.current) menuRef.current?.focus();
    wasOpen.current = open;
  }, [open]);
  function close() {
    setOpen(false);
  }
  // The study desk is its own compact window: no sidebar or footer.
  if (pathname.startsWith("/desk"))
    return (
      <main id="main" className="desk-root">
        {children}
      </main>
    );
  return (
    <div
      className={`app-shell ${desk.open ? "has-desk" : ""} ${collapsed ? "is-collapsed" : ""}`}
    >
      <a className="skip-link" href="#main">
        {t("shell.skip")}
      </a>
      {open && (
        <button
          className="drawer-scrim"
          aria-label={t("shell.closeMenu")}
          onClick={close}
        />
      )}
      <aside
        className={`sidebar ${open ? "is-open" : ""}`}
        aria-label={t("shell.mainNav")}
        role={open ? "dialog" : undefined}
        aria-modal={open || undefined}
        onKeyDown={(e) => {
          if (e.key === "Escape") close();
          if (open && e.key === "Tab") {
            const items = [
              ...e.currentTarget.querySelectorAll<HTMLElement>(
                "a[href], button:not([disabled])",
              ),
            ];
            const first = items[0],
              last = items.at(-1);
            if (e.shiftKey && document.activeElement === first) {
              e.preventDefault();
              last?.focus();
            } else if (!e.shiftKey && document.activeElement === last) {
              e.preventDefault();
              first?.focus();
            }
          }
        }}
      >
        <Link className="brand" href="/" onClick={() => setOpen(false)}>
          <span className="brand-mark">
            <Atom size={24} />
          </span>
          <span className="brand-text">
            CoreLab<span className="brand-dot">.</span>
          </span>
        </Link>
        <button
          type="button"
          className="icon-button sidebar-toggle"
          onClick={toggleRail}
          aria-expanded={!collapsed}
          aria-label={t(
            collapsed ? "shell.expandSidebar" : "shell.collapseSidebar",
          )}
          title={t(collapsed ? "shell.expandSidebar" : "shell.collapseSidebar")}
        >
          {collapsed ? (
            <PanelLeftOpen size={18} />
          ) : (
            <PanelLeftClose size={18} />
          )}
        </button>
        <button
          ref={closeRef}
          className="icon-button drawer-close"
          onClick={close}
          aria-label={t("shell.closeMenu")}
        >
          <PanelLeftClose size={20} />
        </button>
        <div
          className="workspace-label"
          title={`${t("shell.workspace")} · ${t("shell.workspaceSub")}`}
        >
          <span className="workspace-initial">N</span>
          <span className="workspace-name">{t("shell.workspace")}</span>
        </div>
        <div className="nav-caption">{t("shell.captionLearn")}</div>
        <nav>
          {main.map(([href, key, Icon]) => (
            <Link
              key={href}
              href={href}
              title={collapsed ? t(key) : undefined}
              onClick={() => setOpen(false)}
              className={
                (href === "/" ? pathname === "/" : pathname.startsWith(href))
                  ? "nav-link active"
                  : "nav-link"
              }
              aria-current={
                (href === "/" ? pathname === "/" : pathname.startsWith(href))
                  ? "page"
                  : undefined
              }
            >
              <Icon size={18} aria-hidden="true" />
              <span className="nav-text">{t(key)}</span>
            </Link>
          ))}
        </nav>
        <div className="nav-caption">{t("shell.captionMore")}</div>
        <nav>
          {extra.map(([href, key, Icon]) => (
            <Link
              key={href}
              href={href}
              title={collapsed ? t(key) : undefined}
              onClick={() => setOpen(false)}
              className={`nav-link ${pathname.startsWith(href) ? "active" : ""}`}
            >
              <Icon size={18} aria-hidden="true" />
              <span className="nav-text">{t(key)}</span>
            </Link>
          ))}
          {v2Enabled && (
            <Link
              href="/objectives"
              className={`nav-link ${pathname.startsWith("/objectives") ? "active" : ""}`}
              aria-current={
                pathname.startsWith("/objectives") ? "page" : undefined
              }
              onClick={() => setOpen(false)}
            >
              <FlaskConical size={18} aria-hidden="true" />
              <span className="nav-text">{t("nav.lab")}</span>
            </Link>
          )}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-card" title={t("shell.localBody")}>
            <span className="local-dot" />
            <span>{t("shell.localTitle")}</span>
          </div>
          <Link
            href="/settings"
            title={collapsed ? t("nav.settings") : undefined}
            className={`nav-link ${pathname === "/settings" ? "active" : ""}`}
            onClick={() => setOpen(false)}
          >
            <Settings size={18} aria-hidden="true" />
            <span className="nav-text">{t("nav.settings")}</span>
          </Link>
          <div className="version">
            CORELAB <span>{v2Enabled ? "V2 workspace" : "v1.0"}</span>
          </div>
        </div>
      </aside>
      <div className="main-shell" inert={open}>
        <header className="topbar">
          <div className="breadcrumb">
            <button
              ref={menuRef}
              className="icon-button mobile-menu"
              onClick={() => setOpen(true)}
              aria-label={t("shell.openMenu")}
              aria-expanded={open}
            >
              <Menu size={20} />
            </button>
            <span>{t("shell.crumb")}</span>
            <span className="slash">/</span>
            <strong>
              {pathname === "/"
                ? t("nav.dashboard")
                : labels[pathname.split("/")[1]]
                  ? t(labels[pathname.split("/")[1]])
                  : "CoreLab"}
            </strong>
          </div>
          <div className="topbar-right">
            <ThemeToggle />
            <button
              type="button"
              className="button secondary desk-open"
              onClick={() => desk.setOpen(!desk.open)}
              aria-pressed={desk.open}
              title={t("shell.deskHint")}
            >
              <PanelRight size={15} aria-hidden="true" />
              <span>{t("shell.desk")}</span>
            </button>
            <div
              className="lang-switch"
              role="group"
              aria-label={t("shell.language")}
            >
              <Languages size={15} aria-hidden="true" />
              {(["en", "vi"] as const).map((l) => (
                <button
                  key={l}
                  type="button"
                  lang={l}
                  aria-pressed={lang === l}
                  className={lang === l ? "selected" : ""}
                  onClick={() => setLang(l)}
                >
                  {l === "en" ? "EN" : "VI"}
                </button>
              ))}
            </div>
            <span className="topbar-note">
              <span className="local-dot" /> {t("shell.local")}{" "}
              <ArrowUpRight size={13} />
            </span>
          </div>
        </header>
        <main id="main" tabIndex={-1}>
          {children}
        </main>
        <footer className="footer">
          <span>{t("shell.footer1")}</span>
          <span>{t("shell.footer2")}</span>
        </footer>
      </div>
      {desk.open && (
        <DeskPanel
          onClose={() => desk.setOpen(false)}
          onPopOut={() => {
            desk.setOpen(false);
            openDesk();
          }}
        />
      )}
    </div>
  );
}
