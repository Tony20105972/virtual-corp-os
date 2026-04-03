"use client"

import { getBezierPath, type EdgeProps } from "@xyflow/react"

export default function AnimatedEdge({
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
}: EdgeProps) {
  const [edgePath] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  })

  return (
    <path
      d={edgePath}
      fill="none"
      stroke="rgba(255,255,255,0.12)"
      strokeWidth={1.5}
      strokeDasharray="6 4"
      style={{ animation: "flowDash 1.2s linear infinite" }}
    />
  )
}
