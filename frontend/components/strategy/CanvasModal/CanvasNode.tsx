"use client"

import { memo } from "react"
import { motion } from "framer-motion"
import { useProjectStore } from "@/store/projectStore"
import type { CanvasNodeConfig } from "@/lib/canvas/canvasConfig"
import styles from "./styles.module.css"

interface CanvasNodeProps {
  config: CanvasNodeConfig
  content: string
  isSelected: boolean
  delay: number
}

function truncateContent(content: string) {
  return content.length > 60 ? `${content.slice(0, 60)}...` : content
}

export const CanvasNode = memo(function CanvasNode({
  config,
  content,
  isSelected,
  delay,
}: CanvasNodeProps) {
  const selectCanvasNode = useProjectStore((s) => s.selectCanvasNode)

  return (
    <motion.button
      type="button"
      className={`${styles.canvasNode} ${isSelected ? styles.selected : ""}`}
      style={{
        borderColor: config.color,
        gridRow: config.position.row + 1,
        gridColumn: config.position.col + 1,
      }}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{
        delay: delay * 0.05,
        duration: 0.3,
        ease: [0.4, 0, 0.2, 1],
      }}
      whileHover={{ scale: 1.05, boxShadow: "0 18px 36px rgba(10, 15, 30, 0.24)" }}
      whileTap={{ scale: 0.98 }}
      onClick={() => selectCanvasNode(config.id)}
      data-testid={`canvas-node-${config.id}`}
      aria-label={`${config.label} 상세보기`}
      title={config.description}
    >
      <span className={styles.nodeGroup}>{config.group}</span>
      <span className={styles.nodeIcon} style={{ color: config.color }}>
        {config.icon}
      </span>
      <h3 className={styles.nodeLabel}>{config.label}</h3>
      <p className={styles.nodeContent}>{truncateContent(content)}</p>
      {isSelected ? (
        <motion.span
          className={styles.selectedIndicator}
          style={{ background: config.color }}
          layoutId="canvas-selected-indicator"
          data-testid={`selected-indicator-${config.id}`}
        />
      ) : null}
    </motion.button>
  )
})
