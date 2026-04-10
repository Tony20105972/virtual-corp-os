"use client"

import { getCanvasNodesOrdered } from "@/lib/canvas/canvasConfig"
import { useProjectStore } from "@/store/projectStore"
import { CanvasNode } from "./CanvasNode"
import { SidePanel } from "./SidePanel"
import { ActionButtons } from "./ActionButtons"
import styles from "./styles.module.css"

export function ModalContent() {
  const prdJson = useProjectStore((s) => s.prd_json)
  const selectedCanvasNode = useProjectStore((s) => s.selectedCanvasNode)
  const closeCanvasModal = useProjectStore((s) => s.closeCanvasModal)
  const nodes = getCanvasNodesOrdered()

  if (!prdJson) {
    return (
      <div className={styles.content}>
        <header className={styles.header}>
          <h2 id="canvas-modal-title" className={styles.title}>
            CEO Briefing
          </h2>
          <p className={styles.subtitle}>Alex is still preparing the boardroom memo.</p>
        </header>
        <div className={styles.emptyState}>PRD 데이터를 불러올 수 없습니다.</div>
        <ActionButtons />
      </div>
    )
  }

  return (
    <div className={styles.content}>
      <header className={styles.header}>
        <div>
          <h2 id="canvas-modal-title" className={styles.title}>
            CEO Briefing
          </h2>
          <p className={styles.subtitle}>
            Alex structured your company into nine strategy signals for final review.
          </p>
        </div>
        <button
          type="button"
          className={styles.closeIcon}
          onClick={closeCanvasModal}
          aria-label="모달 닫기"
        >
          ✕
        </button>
      </header>

      <div className={styles.mainLayout}>
        <div className={styles.gridContainer}>
          {nodes.map((nodeConfig, index) => (
            <CanvasNode
              key={nodeConfig.id}
              config={nodeConfig}
              content={prdJson[nodeConfig.id] || "생성 중..."}
              isSelected={selectedCanvasNode === nodeConfig.id}
              delay={index}
            />
          ))}
        </div>

        <SidePanel />
      </div>

      <ActionButtons />
    </div>
  )
}
