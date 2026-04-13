"use client"

import { useProjectStore } from "@/store/projectStore"
import styles from "./styles.module.css"

export function ActionButtons() {
  const closeCanvasModal = useProjectStore((s) => s.closeCanvasModal)

  const handleReturnToBriefing = () => {
    closeCanvasModal()
  }

  return (
    <footer className={styles.actionButtons}>
      <button
        type="button"
        className={styles.buttonSecondary}
        onClick={closeCanvasModal}
      >
        닫기
      </button>
      <button
        type="button"
        className={styles.buttonPrimary}
        onClick={handleReturnToBriefing}
      >
        CEO 브리핑으로 돌아가기
      </button>
    </footer>
  )
}
