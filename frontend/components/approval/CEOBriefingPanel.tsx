"use client"

import { useState } from "react"
import { useApprovalApi } from "@/hooks/useApprovalApi"
import { useProjectStore } from "@/store/projectStore"

function sectionStyle(label: string, value: string) {
  return (
    <div style={{ display: "grid", gap: 6 }}>
      <span style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "rgba(148,163,184,0.8)" }}>
        {label}
      </span>
      <span style={{ color: "#E2E8F0", lineHeight: 1.55 }}>{value}</span>
    </div>
  )
}

function normalizeText(value: unknown) {
  return typeof value === "string" ? value : ""
}

function normalizeList(value: unknown) {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : []
}

export function CEOBriefingPanel() {
  const projectId = useProjectStore((state) => state.projectId)
  const status = useProjectStore((state) => state.status)
  const strategySummary = useProjectStore((state) => state.strategySummary)
  const strategyReportReady = useProjectStore((state) => state.strategyReportReady)
  const categoryTags = useProjectStore((state) => state.categoryTags)
  const openCanvasModal = useProjectStore((state) => state.openCanvasModal)
  const setStatus = useProjectStore((state) => state.setStatus)
  const setRevisionCount = useProjectStore((state) => state.setRevisionCount)
  const setLastRevisedItems = useProjectStore((state) => state.setLastRevisedItems)
  const api = useApprovalApi()

  const [isSubmitting, setIsSubmitting] = useState(false)
  const [revisionNote, setRevisionNote] = useState("")

  if (!strategyReportReady) {
    if (status === "strategy_running" || status === "build_pending" || status === "building") {
      return (
        <div style={{ display: "grid", gap: 16 }}>
          <div style={{ color: "#E2E8F0", fontSize: 18, lineHeight: 1.4 }}>
            Alex가 전략 보고서를 정리 중입니다.
          </div>
          <div style={{ color: "#94A3B8", lineHeight: 1.7 }}>
            전략 보고서가 아직 완전히 준비되지 않았습니다. 보고서가 준비되면 여기에서 핵심 한 줄 요약, 타겟 고객, 가치 제안, 수익 모델, 추천 MVP 범위를 검토한 뒤 개발 착수를 지시할 수 있습니다.
          </div>
        </div>
      )
    }

    return (
      <div style={{ color: "#94A3B8", lineHeight: 1.7 }}>
        아이디어 브리프를 입력하면 AI Interviewer가 먼저 질문을 던지고, 그 답변을 바탕으로 CEO 브리핑이 이 영역에 채워집니다.
      </div>
    )
  }

  const headline = normalizeText(strategySummary?.headline)
  const narrative = normalizeText(strategySummary?.summary || strategySummary?.narrative)
  const targetCustomer = normalizeText(strategySummary?.target_customer)
  const valueProposition = normalizeText(strategySummary?.value_proposition)
  const revenueModel = normalizeText(strategySummary?.revenue_model)
  const mvpScope = normalizeList(strategySummary?.mvp_scope)
  const summaryCategoryTags = normalizeList(strategySummary?.category_tags)
  const normalizedCategoryTags = summaryCategoryTags.length > 0 ? summaryCategoryTags : categoryTags
  const risks = normalizeList(strategySummary?.risks)
  const nextSteps = normalizeList(strategySummary?.next_steps)

  const handleApprove = async () => {
    if (!projectId || isSubmitting) return
    setIsSubmitting(true)
    try {
      await api.approveProject(projectId)
      setStatus("build_pending")
    } catch (error) {
      console.error(error)
      window.alert("전략 승인 처리에 실패했습니다.")
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleRevise = async () => {
    if (!projectId || isSubmitting) return
    setIsSubmitting(true)
    try {
      const data = await api.requestRevision(projectId, {
        feedback_option: revisionNote.trim() ? "custom" : "overall_revision",
        custom_feedback: revisionNote.trim() || "핵심 고객과 가치 제안을 다시 정렬해주세요.",
      })
      setStatus("strategy_running")
      setRevisionCount(data.revision_count ?? 0)
      setLastRevisedItems(data.affected_items ?? [])
    } catch (error) {
      console.error(error)
      window.alert(error instanceof Error ? error.message : "전략 수정 요청에 실패했습니다.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div style={{ display: "grid", gap: 18 }}>
      <div style={{ display: "grid", gap: 10 }}>
        <h3 style={{ margin: 0, color: "#F8FAFC", fontSize: 24, lineHeight: 1.1 }}>
          {headline || "전략 핵심 요약을 정리 중입니다."}
        </h3>
        <p style={{ margin: 0, color: "#CBD5E1", lineHeight: 1.75 }}>
          {narrative || "전략 보고서가 아직 완전히 준비되지 않았습니다."}
        </p>
      </div>

      {sectionStyle("핵심 타겟 고객", targetCustomer || "타겟 고객을 정리 중입니다.")}
      {sectionStyle("핵심 가치 제안", valueProposition || "핵심 가치 제안을 정리 중입니다.")}
      {sectionStyle("수익 모델", revenueModel || "수익 모델을 정리 중입니다.")}

      <div style={{ display: "grid", gap: 8 }}>
        <span style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "rgba(148,163,184,0.8)" }}>
          카테고리 태그
        </span>
        {normalizedCategoryTags.length > 0 ? (
          <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
            {normalizedCategoryTags.map((tag) => (
              <span
                key={tag}
                style={{
                  borderRadius: 999,
                  border: "1px solid rgba(96,165,250,0.18)",
                  background: "rgba(15,23,42,0.45)",
                  color: "#DBEAFE",
                  padding: "6px 10px",
                  fontSize: 13,
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        ) : (
          <div style={{ color: "#94A3B8", lineHeight: 1.6 }}>사업 카테고리를 정리 중입니다.</div>
        )}
      </div>

      <div style={{ display: "grid", gap: 8 }}>
        <span style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "rgba(148,163,184,0.8)" }}>
          추천 MVP 범위
        </span>
        {mvpScope.length > 0 ? (
          <div style={{ display: "grid", gap: 8 }}>
            {mvpScope.map((item) => (
              <div
                key={item}
                style={{
                  border: "1px solid rgba(96,165,250,0.18)",
                  borderRadius: 12,
                  background: "rgba(15,23,42,0.5)",
                  padding: "10px 12px",
                  color: "#E2E8F0",
                }}
              >
                {item}
              </div>
            ))}
          </div>
        ) : (
          <div style={{ color: "#94A3B8", lineHeight: 1.6 }}>추천 MVP 범위를 정리 중입니다.</div>
        )}
      </div>

      <div style={{ display: "grid", gap: 8 }}>
        <span style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "rgba(148,163,184,0.8)" }}>
          주요 리스크
        </span>
        {risks.length > 0 ? (
          <ul style={{ margin: 0, paddingLeft: 18, color: "#E2E8F0", lineHeight: 1.7 }}>
            {risks.map((risk) => (
              <li key={risk}>{risk}</li>
            ))}
          </ul>
        ) : (
          <div style={{ color: "#94A3B8", lineHeight: 1.6 }}>주요 리스크를 정리 중입니다.</div>
        )}
      </div>

      <div style={{ display: "grid", gap: 8 }}>
        <span style={{ fontSize: 11, letterSpacing: "0.12em", textTransform: "uppercase", color: "rgba(148,163,184,0.8)" }}>
          다음 단계
        </span>
        {nextSteps.length > 0 ? (
          <ul style={{ margin: 0, paddingLeft: 18, color: "#E2E8F0", lineHeight: 1.7 }}>
            {nextSteps.map((step) => (
              <li key={step}>{step}</li>
            ))}
          </ul>
        ) : (
          <div style={{ color: "#94A3B8", lineHeight: 1.6 }}>다음 실행 단계를 정리 중입니다.</div>
        )}
      </div>

      <button
        type="button"
        onClick={openCanvasModal}
        style={{
          minHeight: 48,
          borderRadius: 14,
          border: "1px solid rgba(96,165,250,0.24)",
          background: "rgba(30,41,59,0.65)",
          color: "#DBEAFE",
          fontWeight: 600,
          cursor: "pointer",
        }}
      >
        Strategy Report / PRD / Canvas 열기
      </button>

      {status === "awaiting_ceo_approval" ? (
        <>
          <textarea
            value={revisionNote}
            onChange={(event) => setRevisionNote(event.target.value)}
            placeholder="수정이 필요하다면 CEO 관점에서 조정 방향을 남겨주세요."
            rows={4}
            style={{
              width: "100%",
              borderRadius: 14,
              border: "1px solid rgba(148,163,184,0.18)",
              background: "rgba(15,23,42,0.65)",
              color: "#F8FAFC",
              padding: 14,
              resize: "vertical",
            }}
          />

          <div style={{ display: "grid", gap: 10 }}>
            <button
              type="button"
              onClick={handleApprove}
              disabled={isSubmitting}
              style={{
                minHeight: 50,
                borderRadius: 14,
                border: "none",
                background: "linear-gradient(135deg, #22C55E, #16A34A)",
                color: "white",
                fontWeight: 700,
                cursor: "pointer",
              }}
            >
              이 범위로 개발팀 착수
            </button>
            <button
              type="button"
              onClick={handleRevise}
              disabled={isSubmitting}
              style={{
                minHeight: 48,
                borderRadius: 14,
                border: "1px solid rgba(248,113,113,0.24)",
                background: "rgba(127,29,29,0.18)",
                color: "#FCA5A5",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              전략 수정 요청
            </button>
          </div>
        </>
      ) : null}
    </div>
  )
}
