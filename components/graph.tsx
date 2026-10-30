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
  const [focus, setFocus] = useState("");
  const [selected, setSelected] = useState("");
  const { nodes, edges } = useMemo(() => {
    const selectedTopics = focus
      ? [focus, ...ancestors(focus)].map((id) => topicMap[id])
      : topics.filter(
          (t) =>
            t.domain === domain &&
            (!query ||
              `${t.id} ${t.title}`
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
        position: { x: l * 270, y: row * 110 },
        data: {
          label: (
            <div>
              <span className="mono">{id}</span>
              <strong>{topicMap[id].title}</strong>
              <small>
                {mastery[id].level
                  ? `Verified L${mastery[id].level}`
                  : "Unassessed"}
              </small>
            </div>
          ),
        },
        style: {
          background: mastery[id].level ? "#15281f" : "#1b1f26",
          border: `1px solid ${mastery[id].level ? "#36714d" : "#3f4652"}`,
          color: "#f3f4f6",
          width: 220,
          borderRadius: 10,
        },
        ariaLabel: `${id} ${topicMap[id].title}`,
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
  }, [domain, query, priority, status, focus, mastery]);
  return (
    <section className="graph-section">
      <div className="between">
        <p className="small muted">
          {focus ? "Selected prerequisite chain" : `Scope: ${domain}`} ·{" "}
          {nodes.length} nodes · drag to pan, scroll to zoom.
        </p>
        <select
          aria-label="Focus prerequisite chain"
          value={focus}
          onChange={(e) => {
            setFocus(e.target.value);
            setSelected("");
          }}
        >
          <option value="">Current domain</option>
          {topics.map((t) => (
            <option value={t.id} key={t.id}>
              {t.id} · {t.title}
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
              {selected} · {topicMap[selected].title}
            </h2>
            <Status mastery={mastery[selected]} />
          </div>
          <p>Prerequisites</p>
          <TopicChips ids={topicMap[selected].prerequisites} />
          <Link className="button" href={`/lessons/${selected}`}>
            Open topic details
          </Link>
        </div>
      )}
      <p className="small muted">
        Select a node to inspect it. Prerequisites outside the domain remain
        visible to preserve relationships. The list provides equivalent keyboard
        navigation.
      </p>
    </section>
  );
}
