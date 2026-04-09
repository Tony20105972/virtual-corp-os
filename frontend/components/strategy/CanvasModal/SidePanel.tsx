"use client"

import { useEffect, useState } from "react"
import { AnimatePresence, motion } from "framer-motion"
import { CANVAS_NODES } from "@/lib/canvas/canvasConfig"
import { useProjectStore } from "@/store/projectStore"
import styles from "./styles.module.css"

export function SidePanel() {
  const selectedCanvasNode = useProjectStore((s) => s.selectedCanvasNode)
  const selectCanvasNode = useProjectStore((s) => s.selectCanvasNode)
  const prdJson = useProjectStore((s) => s.prd_json)
  const [isMobile, setIsMobile] = useState(false)

  useEffect(() => {
    const mediaQuery = window.matchMedia("(max-width: 768px)")
    const sync = () => setIsMobile(mediaQuery.matches)

    sync()
    mediaQuery.addEventListener("change", sync)
    return () => mediaQuery.removeEventListener("change", sync)
  }, [])

  if (!selectedCanvasNode || !prdJson) return null

  const nodeConfig = CANVAS_NODES[selectedCanvasNode]
  const content = prdJson[selectedCanvasNode]

  return (
    <AnimatePresence mode="wait">
      <motion.aside
        key={selectedCanvasNode}
        className={styles.sidePanel}
        initial={isMobile ? { y: "100%" } : { x: "100%" }}
        animate={isMobile ? { y: 0 } : { x: 0 }}
        exit={isMobile ? { y: "100%" } : { x: "100%" }}
        transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
        data-testid="side-panel"
      >
        <div className={styles.sidePanelHeader}>
          <button
            type="button"
            className={styles.backButton}
            onClick={() => selectCanvasNode(null)}
          >
            ← 뒤로
          </button>
        </div>

        <div className={styles.sidePanelBody}>
          <div className={styles.sidePanelIcon} style={{ color: nodeConfig.color }}>
            {nodeConfig.icon}
          </div>
          <h3 className={styles.sidePanelTitle}>{nodeConfig.label}</h3>
          <p className={styles.sidePanelDescription}>{nodeConfig.description}</p>
          <div className={styles.sidePanelText}>{content}</div>
        </div>
      </motion.aside>
    </AnimatePresence>
  )
}
