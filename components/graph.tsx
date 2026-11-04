"use client";
import { useEffect, useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
  Position,
  useNodesState,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import Link from "next/link";
import { ancestors, topics, topicMap } from "@/lib/curriculum";
import type { Mastery } from "@/lib/types";
import { TopicChips, Status } from "./ui";
import { useCore } from "./provider";
import { useI18n } from "@/lib/i18n";
import { domainTone } from "./domain-theme";
import { layoutGraph } from "@/lib/graph-layout";
// Card height estimate for layout: wraps the bold title at ~22 characters a
// line (290px card), plus the code line, status pill and padding.
function cardHeight(text: string) {
  let lines = 1;
  let width = 0;
  for (const word of text.split(/\s+/)) {
    if (width && width + 1 + word.length > 22) {
      lines++;
      width = word.length;
    } else width += (width ? 1 : 0) + word.length;
  }
  return 104 + 28 * lines;
}
// Minimap colors mirror the --domain-accent values in globals.css.
const toneAccent: Record<string, string> = {
  blue: "#93c5fd",
  sky: "#7dd3fc",
  violet: "#c4b5fd",
  teal: "#5eead4",
  orange: "#fdba74",
  rose: "#f9a8d4",
  indigo: "#a5b4fc",
  amber: "#fde68a",
  lime: "#bef264",
  red: "#fca5a5",
  green: "#4ade80",
  fuchsia: "#f0abfc",
};
const columnWidth = 400;
export function Graph({
  domain,
  query,
  priority,
  status,
  mastery,
}: {
  domain: string;
  query: string;
  priority: string;
  status: string;
  mastery: Record<string, Mastery>;
}) {
  const router = useRouter();
  const { t } = useI18n();
  const { title } = useCore();
  const [focus, setFocus] = useState("");
  const [selected, setSelected] = useState("");
  const [hovered, setHovered] = useState("");
  const { nodes, links, items } = useMemo(() => {
    const selectedTopics = focus
      ? [focus, ...ancestors(focus)].map((id) => topicMap[id])
      : topics.filter(
          (t) =>
            (!domain || t.domain === domain) &&
            (!query ||
              `${t.id} ${t.title} ${title(t.id)}`
                .toLowerCase()
                .includes(query.toLowerCase())) &&
            (!priority || t.priority === priority) &&
            (!status || mastery[t.id].status === status),
        );
    const inScope = new Set(selectedTopics.map((t) => t.id));
    const ids = new Set(
      selectedTopics.flatMap((t) => [t.id, ...t.prerequisites]),
    );
    const its = [...ids].map((id) => ({
      id,
      prerequisites: topicMap[id].prerequisites,
    }));
    const placed = layoutGraph(its, {
      height: (id) => cardHeight(title(id)),
    });
    const ns: Node[] = placed.map(({ id, column, y }) => {
      return {
        id,
        position: { x: column * columnWidth, y },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
        className: "graph-node",
        data: {
          label: (
            <div
              className="graph-card"
              data-domain-tone={domainTone(topicMap[id].domain)}
              data-context={inScope.has(id) ? undefined : "true"}
            >
              <span className="mono">{id}</span>
              <strong>{title(id)}</strong>
              <Status mastery={mastery[id]} />
            </div>
          ),
        },
        style: { width: 290, padding: 0, background: "none", border: 0 },
        ariaLabel: `${id} ${title(id)}`,
      };
    });
    const ls = [...ids].flatMap((id) =>
      topicMap[id].prerequisites
        .filter((p) => ids.has(p))
        .map((p) => ({ source: p, target: id })),
    );
    return { nodes: ns, links: ls, items: its };
  }, [domain, query, priority, status, focus, mastery, title]);
  // Controlled nodes: titles load after a language switch and statuses change,
  // so labels refresh in place (dragged positions reset only then).
  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState(nodes);
  useEffect(() => setFlowNodes(nodes), [nodes, setFlowNodes]);
  // Once the cards are measured, stack each column by its real heights.
  const relaid = useRef<Node[] | null>(null);
  useEffect(() => {
    if (relaid.current === nodes || flowNodes.length !== nodes.length) return;
    if (
      !flowNodes.every((n, i) => n.data === nodes[i].data && n.measured?.height)
    )
      return;
    relaid.current = nodes;
    const heights = new Map(flowNodes.map((n) => [n.id, n.measured!.height!]));
    const at = new Map(
      layoutGraph(items, { height: (id) => heights.get(id)! }).map((p) => [
        p.id,
        p,
      ]),
    );
    setFlowNodes((ns) =>
      ns.map((n) => ({
        ...n,
        position: { x: at.get(n.id)!.column * columnWidth, y: at.get(n.id)!.y },
      })),
    );
  }, [flowNodes, nodes, items, setFlowNodes]);
  // Highlight the arrows of the hovered (or selected) topic and fade the rest.
  const active = [hovered, selected].find(
    (id) => id && nodes.some((n) => n.id === id),
  );
  const edges: Edge[] = useMemo(
    () =>
      links.map(({ source, target }) => {
        const on = active && (source === active || target === active);
        const color = on ? "#f59e0b" : "#7d8795";
        return {
          id: `${source}-${target}`,
          source,
          target,
          zIndex: on ? 1 : 0,
          markerEnd: { type: MarkerType.ArrowClosed, color },
          style: {
            stroke: on ? color : "#626d7d",
            strokeWidth: on ? 2.5 : 1.25,
            opacity: active && !on ? 0.15 : 1,
          },
        };
      }),
    [links, active],
  );
  return (
    <section className="graph-section">
      <div className="between">
        <p className="small muted">
          {focus
            ? t("graph.chain")
            : t("graph.scope", { domain: domain || t("cat.allDomains") })}{" "}
          · {t("graph.nodes", { n: nodes.length })}
        </p>
        <select
          aria-label={t("graph.focus")}
          value={focus}
          onChange={(e) => {
            setFocus(e.target.value);
            setSelected("");
          }}
        >
          <option value="">{t("graph.currentDomain")}</option>
          {topics.map((t) => (
            <option value={t.id} key={t.id}>
              {t.id} · {title(t.id)}
            </option>
          ))}
        </select>
      </div>
      <div className="graph-canvas">
        <ReactFlow
          key={`${domain}-${focus}-${query}-${priority}-${status}`}
          nodes={flowNodes}
          onNodesChange={onNodesChange}
          edges={edges}
          edgesFocusable={false}
          colorMode="dark"
          fitView
          fitViewOptions={{
            padding: 0.1,
            minZoom: domain || focus ? 0.6 : 0.2,
            maxZoom: 1,
          }}
          minZoom={0.15}
          maxZoom={1.8}
          onNodeClick={(_, node) => setSelected(node.id)}
          onNodeMouseEnter={(_, node) => setHovered(node.id)}
          onNodeMouseLeave={() => setHovered("")}
          onPaneClick={() => setSelected("")}
          onNodeDoubleClick={(_, node) => router.push(`/lessons/${node.id}`)}
        >
          <Background gap={24} color="#323946" />
          <Controls showInteractive={false} />
          <MiniMap
            pannable
            zoomable
            nodeColor={(n) =>
              toneAccent[domainTone(topicMap[n.id]?.domain)] ?? "#626d7d"
            }
            maskColor="rgba(13,15,18,.7)"
          />
        </ReactFlow>
      </div>
      <ul className="graph-legend" aria-label={t("graph.legend")}>
        {[...new Set(nodes.map((n) => topicMap[n.id].domain))].map((d) => (
          <li key={d} data-domain-tone={domainTone(d)}>
            <span className="graph-swatch" />
            {d}
          </li>
        ))}
        {!focus &&
          domain &&
          nodes.some((n) => topicMap[n.id].domain !== domain) && (
            <li>
              <span className="graph-swatch dashed" />
              {t("graph.outside")}
            </li>
          )}
      </ul>
      {selected && (
        <div className="panel graph-detail">
          <div className="between">
            <h2>
              {selected} · {title(selected)}
            </h2>
            <Status mastery={mastery[selected]} />
          </div>
          <p>{t("graph.prereqs")}</p>
          <TopicChips ids={topicMap[selected].prerequisites} />
          <Link className="button" href={`/lessons/${selected}`}>
            {t("graph.open")}
          </Link>
        </div>
      )}
      <p className="small muted">{t("graph.note")}</p>
    </section>
  );
}
