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
} from "lucide-react";
const main = [
  ["/", "Dashboard", LayoutDashboard],
  ["/roadmap", "Roadmap", Network],
  ["/lessons", "Lessons", BookOpen],
  ["/assessments", "Assessments", ClipboardCheck],
] as const;
const extra = [
  ["/paths", "Learning paths", Route],
  ["/practice", "Practice", FlaskConical],
  ["/tutor", "AI Tutor handoff", MessageSquare],
  ["/sources", "References", Library],
] as const;
const labels: Record<string, string> = {
  roadmap: "Roadmap",
  lessons: "Lessons",
  assessments: "Assessments",
  paths: "Learning paths",
  practice: "Practice",
  tutor: "AI Tutor handoff",
  settings: "Data & settings",
  sources: "References",
};
export function Shell({ children }: { children: ReactNode }) {
  const pathname = usePathname(),
    [open, setOpen] = useState(false);
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
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip navigation
      </a>
      {open && (
        <button
          className="drawer-scrim"
          aria-label="Close menu"
          onClick={close}
        />
      )}
      <aside
        className={`sidebar ${open ? "is-open" : ""}`}
        aria-label="Main navigation"
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
          <span>
            CoreLab<span className="brand-dot">.</span>
          </span>
        </Link>
        <button
          ref={closeRef}
          className="icon-button drawer-close"
          onClick={close}
          aria-label="Close menu"
        >
          <PanelLeftClose size={20} />
        </button>
        <div className="workspace-label">
          <span className="workspace-initial">N</span>
          <div>
            Personal workspace<small>Robotics & AI research</small>
          </div>
          <span className="local-dot" />
        </div>
        <div className="nav-caption">WORKSPACE</div>
        <nav>
          {main.map(([href, label, Icon]) => (
            <Link
              key={href}
              href={href}
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
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="nav-caption">LEARNING TOOLS</div>
        <nav>
          {extra.map(([href, label, Icon]) => (
            <Link
              key={href}
              href={href}
              onClick={() => setOpen(false)}
              className={`nav-link ${pathname.startsWith(href) ? "active" : ""}`}
            >
              <Icon size={18} />
              {label}
            </Link>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="local-card">
            <span className="local-dot" />
            <strong>Local-first. Yours.</strong>
            <p>
              Your data stays on your machine.
              <br />
              No cloud, no API.
            </p>
          </div>
          <Link
            href="/settings"
            className={`nav-link ${pathname === "/settings" ? "active" : ""}`}
            onClick={() => setOpen(false)}
          >
            <Settings size={18} />
            Data & settings
          </Link>
          <div className="version">
            CORELAB <span>v1.0</span>
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
              aria-label="Open menu"
              aria-expanded={open}
            >
              <Menu size={20} />
            </button>
            <span>Workspace</span>
            <span className="slash">/</span>
            <strong>
              {pathname === "/"
                ? "Dashboard"
                : (labels[pathname.split("/")[1]] ?? "CoreLab")}
            </strong>
          </div>
          <span className="topbar-note">
            <span className="local-dot" /> Local workspace{" "}
            <ArrowUpRight size={13} />
          </span>
        </header>
        <main id="main" tabIndex={-1}>
          {children}
        </main>
        <footer className="footer">
          <span>Understand principles. Implement independently. Verify.</span>
          <span>
            Diagnostic → Learn → Derive → Implement → Verify → Transfer
          </span>
        </footer>
      </div>
    </div>
  );
}
