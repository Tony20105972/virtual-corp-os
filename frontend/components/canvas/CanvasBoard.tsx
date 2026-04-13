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
import { CEOBriefingPanel } from "@/components/approval/CEOBriefingPanel"
import { buildInitialNodes, buildInitialEdges } from "@/lib/canvas/nodeConfig"
import { useProjectStore } from "@/store/projectStore"
import { useInterviewStore } from "@/store/interviewStore"
import { useSSE } from "@/lib/sse/useSSE"
import { useProjectPolling } from "@/hooks/useProjectPolling"
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
  const strategySummary = useProjectStore((s) => s.strategySummary)
  const strategyReportReady = useProjectStore((s) => s.strategyReportReady)
  const projectStatus = useProjectStore((s) => s.status)
  const nodeStatuses = useProjectStore((s) => s.nodeStatuses)
  const interviewStatus = useInterviewStore((s) => s.status)
  const idea = useInterviewStore((s) => s.idea)

  useSSE(projectId)
  useProjectPolling(projectId)

  const isWarRoom = interviewStatus === "done" || projectStatus !== "intake_pending"
  const currentStage = strategyReportReady
    ? "CEO Briefing Ready"
    : projectStatus === "strategy_running"
      ? "Strategy Report In Progress"
      : isWarRoom
        ? "Interview In Progress"
        : "Boardroom Intake"

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
                    {strategyReportReady
                      ? "전략 보고서가 준비되었습니다. 보고서를 검토한 뒤 개발팀 착수를 승인할 수 있습니다."
                      : projectStatus === "strategy_running"
                        ? "Alex가 전략 보고서를 정리 중입니다."
                        : "먼저 아이디어를 입력하고 AI Interviewer 질문에 답하면 CEO 브리핑이 만들어집니다."}
                  </span>
                </div>
                <div className={styles.briefItem}>
                  <span className={styles.briefLabel}>Boardroom Signal</span>
                  <span className={styles.briefValue}>
                    {strategyReportReady
                      ? "전략 없는 승인은 금지됩니다. 보고서를 먼저 읽고, 그 다음 개발 착수를 결정하세요."
                      : "질문은 사업 아이디어 유형에 맞춰 동적으로 바뀝니다."}
                  </span>
                </div>
              </div>

              <CEOBriefingPanel />

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
