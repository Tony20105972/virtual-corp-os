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
            Alex&apos;s Business Strategy
          </h2>
          <p className={styles.subtitle}>전략 캔버스를 준비하는 중입니다.</p>
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
            Alex&apos;s Business Strategy
          </h2>
          <p className={styles.subtitle}>
            아이디어를 9가지 전략 요소로 구조화해 한눈에 보여드립니다.
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
