"use client"

import { useProjectStore } from "@/store/projectStore"
import styles from "./styles.module.css"

export function ActionButtons() {
  const closeCanvasModal = useProjectStore((s) => s.closeCanvasModal)

  const handleApprovalProceed = () => {
    closeCanvasModal()
    console.log("[Day11] CEO approval modal placeholder")
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
        onClick={handleApprovalProceed}
      >
        승인 진행 →
      </button>
    </footer>
  )
}
