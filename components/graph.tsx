"use client";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  MarkerType,
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
  const { nodes, edges } = useMemo(() => {
    const selectedTopics = focus
      ? [focus, ...ancestors(focus)].map((id) => topicMap[id])
      : topics.filter(
          (t) =>
            t.domain === domain &&
            (!query ||
              `${t.id} ${t.title} ${title(t.id)}`
                .toLowerCase()
                .includes(query.toLowerCase())) &&
            (!priority || t.priority === priority) &&
            (!status || mastery[t.id].status === status),
        );
    const ids = new Set(
      selectedTopics.flatMap((t) => [t.id, ...t.prerequisites]),
    );
    const levels: Record<string, number> = {};
    function level(id: string): number {
      return (levels[id] ??= topicMap[id].prerequisites.length
        ? Math.max(...topicMap[id].prerequisites.map(level)) + 1
        : 0);
    }
    const rows: Record<number, number> = {};
    const ns: Node[] = [...ids].map((id) => {
      const l = level(id);
      const row = rows[l] ?? 0;
      rows[l] = row + 1;
      return {
        id,
        position: { x: l * 340, y: row * 170 },
        data: {
          label: (
            <div>
              <span className="mono">{id}</span>
              <strong>{title(id)}</strong>
              <small>
                {mastery[id].level
                  ? t("status.mastered")
                  : mastery[id].status === "in_progress"
                    ? t("status.practised")
                    : t("status.notStarted")}
              </small>
            </div>
          ),
        },
        style: {
          background: mastery[id].level ? "#15281f" : "#1b1f26",
          border: `1px solid ${mastery[id].level ? "#36714d" : "#3f4652"}`,
          color: "#f3f4f6",
          width: 290,
          borderRadius: 10,
          fontSize: 16,
          padding: 12,
        },
        ariaLabel: `${id} ${title(id)}`,
      };
    });
    const es: Edge[] = [...ids].flatMap((id) =>
      topicMap[id].prerequisites
        .filter((p) => ids.has(p))
        .map((p) => ({
          id: `${p}-${id}`,
          source: p,
          target: id,
          markerEnd: { type: MarkerType.ArrowClosed, color: "#7d8795" },
          style: { stroke: "#626d7d" },
        })),
    );
    return { nodes: ns, edges: es };
  }, [domain, query, priority, status, focus, mastery, t, title]);
  return (
    <section className="graph-section">
      <div className="between">
        <p className="small muted">
          {focus ? t("graph.chain") : t("graph.scope", { domain })} ·{" "}
          {t("graph.nodes", { n: nodes.length })}
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
          defaultNodes={nodes}
          defaultEdges={edges}
          colorMode="dark"
          fitView
          fitViewOptions={{ padding: 0.1, minZoom: 0.6, maxZoom: 1 }}
          minZoom={0.15}
          maxZoom={1.8}
          onNodeClick={(_, node) => setSelected(node.id)}
          onNodeDoubleClick={(_, node) => router.push(`/lessons/${node.id}`)}
        >
          <Background gap={24} color="#323946" />
          <Controls showInteractive={false} />
          <MiniMap
            pannable
            zoomable
            nodeColor="#626d7d"
            maskColor="rgba(13,15,18,.7)"
          />
        </ReactFlow>
      </div>
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
