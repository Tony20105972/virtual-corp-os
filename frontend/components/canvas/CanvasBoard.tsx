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
import MagicBar from "./MagicBar"
import AIInterviewer from "./AIInterviewer"
import CanvasModal from "@/components/strategy/CanvasModal"
import { buildInitialNodes, buildInitialEdges } from "@/lib/canvas/nodeConfig"
import { useProjectStore } from "@/store/projectStore"
import { useInterviewStore } from "@/store/interviewStore"
import { useSSE } from "@/lib/sse/useSSE"
import type { AgentNodeData } from "./AgentNode"
import type { Node } from "@xyflow/react"
import styles from "./boardroom.module.css"

const nodeTypes = { agentNode: AgentNode }
const edgeTypes = { animatedEdge: AnimatedEdge }

const HERO_LINES = [
  { agent: "Alex", color: "var(--blue)", text: "Positioning defined." },
  { agent: "Jamie", color: "var(--green)", text: "Landing page generating..." },
  { agent: "Sam", color: "var(--amber)", text: "QA in progress." },
  { agent: "Aria", color: "var(--violet)", text: "Launch copy ready." },
]

export default function CanvasBoard() {
  const nodes = useMemo(() => buildInitialNodes(), [])
  const edges = useMemo(() => buildInitialEdges(), [])
  const projectId = useProjectStore((s) => s.projectId)
  const prdJson = useProjectStore((s) => s.prd_json)
  const nodeStatuses = useProjectStore((s) => s.nodeStatuses)
  const interviewStatus = useInterviewStore((s) => s.status)
  const idea = useInterviewStore((s) => s.idea)

  useSSE(projectId)

  const isWarRoom = interviewStatus === "done"
  const currentStage = prdJson ? "CEO Approval Ready" : isWarRoom ? "Company Executing" : "Boardroom Intake"

  return (
    <div className={styles.boardroom}>
      <div className={styles.ambientGlow} />

      <div className={styles.chrome}>
        <header className={styles.topBar}>
          <div className={styles.brandBlock}>
            <p className={styles.eyebrow}>Virtual Corp OS</p>
            <h1 className={styles.brandTitle}>
              {isWarRoom ? "AI Boardroom" : "Build your company like a CEO"}
            </h1>
          </div>

          <div className={styles.stageCluster}>
            <span className={`${styles.stagePill} ${styles.stagePillActive}`}>{currentStage}</span>
            <span className={styles.stagePill}>
              {idea ? `Project · ${idea}` : "Project · Awaiting brief"}
            </span>
          </div>

          <div className={styles.topBarSpacer} />

          {isWarRoom ? <MagicBar compact /> : null}
        </header>

        <main className={styles.main}>
          <aside className={`${styles.panel} ${styles.sidebar}`}>
            <AgentChat />
          </aside>

          <section className={styles.canvasPanel}>
            <div
              className={`${styles.canvasViewport} ${!isWarRoom ? styles.canvasViewportMuted : ""}`}
            >
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
                    background: "rgba(8, 13, 24, 0.88)",
                    border: "1px solid rgba(255,255,255,0.08)",
                  }}
                />
                <MiniMap
                  style={{
                    background: "rgba(8, 13, 24, 0.88)",
                    border: "1px solid rgba(255,255,255,0.08)",
                  }}
                  nodeColor={(n) =>
                    ((n as Node<AgentNodeData>).data?.color ?? "#94A3B8") + "66"
                  }
                />
              </ReactFlow>
            </div>

            {!isWarRoom ? <div className={styles.canvasScrim} /> : null}

            <div className={styles.canvasHint}>
              <span>Strategy → PRD → Canvas</span>
              <span>React Flow stays live in the room</span>
            </div>
          </section>

          <aside className={`${styles.panel} ${styles.sidebar}`}>
            <div className={styles.panelHeader}>
              <div>
                <p className={styles.eyebrow}>CEO Briefing</p>
                <h2 className={styles.panelTitle}>{idea || "Waiting for company brief"}</h2>
              </div>
            </div>

            <div className={styles.panelBody}>
              <div className={styles.briefList}>
                <div className={styles.briefItem}>
                  <span className={styles.briefLabel}>Strategy Status</span>
                  <span className={styles.briefValue}>
                    {prdJson
                      ? "Strategic brief is ready. Open the strategy report for a full review."
                      : "Your agents will turn the brief into a strategy memo and execution canvas."}
                  </span>
                </div>
                <div className={styles.briefItem}>
                  <span className={styles.briefLabel}>Boardroom Signal</span>
                  <span className={styles.briefValue}>
                    {isWarRoom
                      ? "The canvas is active. Strategy can now move toward approval and build."
                      : "Answer five decisions quickly so the room can move from intent to execution."}
                  </span>
                </div>
              </div>

              <div className={styles.summaryBox}>
                <div className={styles.summaryLine}>
                  <span>Intake</span>
                  <span className={styles.summaryTone}>{nodeStatuses.intake}</span>
                </div>
                <div className={styles.summaryLine}>
                  <span>Strategy</span>
                  <span className={styles.summaryTone}>{nodeStatuses.strategy}</span>
                </div>
                <div className={styles.summaryLine}>
                  <span>Build</span>
                  <span className={styles.summaryTone}>{nodeStatuses.build}</span>
                </div>
                <div className={styles.summaryLine}>
                  <span>Deploy</span>
                  <span className={styles.summaryTone}>{nodeStatuses.deploy}</span>
                </div>
              </div>
            </div>
          </aside>
        </main>
      </div>

      {!isWarRoom ? (
        <div className={styles.hero}>
          <div className={styles.heroInner}>
            <div className={styles.heroText}>
              <p className={styles.eyebrow}>Your AI Boardroom</p>
              <h2 className={styles.heroTitle}>Step into a company already in motion.</h2>
              <p className={styles.heroSubtitle}>
                Brief the room once. Alex defines the strategy, Jamie shapes the product,
                Sam checks the quality, and the canvas keeps the whole company visible.
              </p>
            </div>

            <div className={styles.heroFeed}>
              {HERO_LINES.map((line) => (
                <div key={line.agent} className={styles.heroLine}>
                  <span className={styles.heroAgent} style={{ color: line.color }}>
                    {line.agent}
                  </span>
                  <span>{line.text}</span>
                </div>
              ))}
            </div>

            <MagicBar className={styles.heroMagicBar} />
          </div>
        </div>
      ) : null}

      <AIInterviewer />
      <CanvasModal />
    </div>
  )
}
