"use client"

import { useMemo } from "react"
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  BackgroundVariant,
} from "@xyflow/react"
import "@xyflow/react/dist/style.css"
import AgentNode from "./AgentNode"
import AnimatedEdge from "./edges/AnimatedEdge"
import AgentChat from "./AgentChat"
import { buildInitialNodes, buildInitialEdges } from "@/lib/canvas/nodeConfig"
import { useProjectStore } from "@/store/projectStore"
import { useSSE } from "@/lib/sse/useSSE"
import type { AgentNodeData } from "./AgentNode"
import type { Node } from "@xyflow/react"

const nodeTypes = { agentNode: AgentNode }
const edgeTypes = { animatedEdge: AnimatedEdge }

export default function CanvasBoard() {
  const nodes     = useMemo(() => buildInitialNodes(), [])
  const edges     = useMemo(() => buildInitialEdges(), [])
  const projectId = useProjectStore((s) => s.projectId)
  useSSE(projectId)

  return (
    <div style={{ width: "100vw", height: "100vh", background: "var(--navy)", position: "relative" }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
      >
        <Background
          variant={BackgroundVariant.Lines}
          gap={60}
          color="rgba(255,255,255,0.04)"
        />
        <Controls
          style={{
            background: "var(--navy2)",
            border: "1px solid var(--line)",
          }}
        />
        <MiniMap
          style={{
            background: "var(--navy2)",
            border: "1px solid var(--line)",
          }}
          nodeColor={(n) =>
            ((n as Node<AgentNodeData>).data?.color ?? "#94A3B8") + "66"
          }
        />
      </ReactFlow>

      <AgentChat />
    </div>
  )
}
