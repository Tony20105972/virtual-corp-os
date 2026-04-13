"use client"

import { useEffect, useRef } from "react"
import { useProjectStore } from "@/store/projectStore"
import { useApprovalApi } from "./useApprovalApi"

export function useProjectPolling(projectId: string | null) {
  const status = useProjectStore((state) => state.status)
  const setProjectId = useProjectStore((state) => state.setProjectId)
  const setStatus = useProjectStore((state) => state.setStatus)
  const setRevisionCount = useProjectStore((state) => state.setRevisionCount)
  const setLastRevisedItems = useProjectStore((state) => state.setLastRevisedItems)
  const setPrdJson = useProjectStore((state) => state.setPrdJson)
  const setStrategySummary = useProjectStore((state) => state.setStrategySummary)
  const setStrategyReportReady = useProjectStore((state) => state.setStrategyReportReady)
  const setNodeStatus = useProjectStore((state) => state.setNodeStatus)
  const setPollingError = useProjectStore((state) => state.setPollingError)
  const api = useApprovalApi()
  const intervalRef = useRef<number | null>(null)
  const activeProjectRef = useRef<string | null>(null)

  useEffect(() => {
    if (intervalRef.current) {
      window.clearInterval(intervalRef.current)
      intervalRef.current = null
    }
    activeProjectRef.current = projectId

    if (!projectId) return
    if (
      status !== "strategy_running" &&
      status !== "build_pending" &&
      status !== "building" &&
      status !== "awaiting_payment_or_deploy_approval" &&
      status !== "deploying"
    ) return

    intervalRef.current = window.setInterval(async () => {
      try {
        if (activeProjectRef.current !== projectId) return
        const data = await api.getStatus(projectId)
        setPollingError(null)
        setRevisionCount(data.revision_count ?? 0)
        setLastRevisedItems(data.last_revised_items ?? [])
        if (data.prd_json) setPrdJson(data.prd_json as never)
        if (data.strategy_summary) setStrategySummary(data.strategy_summary as never)
        setStrategyReportReady(Boolean(data.strategy_report_ready))

        if (data.status !== status) {
          setStatus(data.status)
          if (data.status === "strategy_running") setNodeStatus("strategy", "processing")
          if (data.status === "awaiting_ceo_approval") {
            setNodeStatus("strategy", "done")
            if (intervalRef.current) window.clearInterval(intervalRef.current)
            intervalRef.current = null
          }
          if (data.status === "build_pending" || data.status === "building") {
            setNodeStatus("build", "processing")
          }
          if (data.status === "awaiting_payment_or_deploy_approval") {
            setNodeStatus("build", "done")
          }
          if (data.status === "deploying") {
            setNodeStatus("deploy", "processing")
          }
          if (data.status === "complete") {
            setNodeStatus("deploy", "done")
            if (intervalRef.current) window.clearInterval(intervalRef.current)
            intervalRef.current = null
          }
        }
      } catch (error) {
        const statusCode = (error as Error & { status?: number }).status
        console.error("Polling error:", error)
        if (statusCode === 404 && activeProjectRef.current === projectId) {
          setPollingError("프로젝트 생성 또는 저장에 실패했습니다. 새로 다시 시도해주세요.")
          setStatus("error")
          setProjectId(null)
          if (intervalRef.current) window.clearInterval(intervalRef.current)
          intervalRef.current = null
          return
        }
      }
    }, 1000)

    return () => {
      if (intervalRef.current) {
        window.clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [
    api,
    projectId,
    setNodeStatus,
    setPollingError,
    setPrdJson,
    setProjectId,
    setLastRevisedItems,
    setRevisionCount,
    setStatus,
    setStrategyReportReady,
    setStrategySummary,
    status,
  ])
}
