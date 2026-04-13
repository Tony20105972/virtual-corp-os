"use client"

import { useState } from "react"
import { useProjectStore } from "@/store/projectStore"
import { FEEDBACK_OPTIONS } from "@/types/approval"
import { useApprovalApi } from "@/hooks/useApprovalApi"
import styles from "./FeedbackSelector.module.css"

interface Props {
  onBack: () => void
}

export function FeedbackSelector({ onBack }: Props) {
  const selectedFeedback = useProjectStore((state) => state.selectedFeedback)
  const customFeedback = useProjectStore((state) => state.customFeedback)
  const setSelectedFeedback = useProjectStore((state) => state.setSelectedFeedback)
  const setCustomFeedback = useProjectStore((state) => state.setCustomFeedback)
  const setStatus = useProjectStore((state) => state.setStatus)
  const setRevisionCount = useProjectStore((state) => state.setRevisionCount)
  const setLastRevisedItems = useProjectStore((state) => state.setLastRevisedItems)
  const closeApprovalModal = useProjectStore((state) => state.closeApprovalModal)
  const projectId = useProjectStore((state) => state.projectId)
  const api = useApprovalApi()

  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (!selectedFeedback || !projectId) return

    if (selectedFeedback.value === "custom" && customFeedback.trim().length < 10) {
      window.alert("구체적인 피드백을 10자 이상 입력해주세요")
      return
    }

    setIsSubmitting(true)
    try {
      const data = await api.requestRevision(projectId, {
        feedback_option: selectedFeedback.value,
        custom_feedback: customFeedback.trim() || null,
      })
      setStatus("strategy_running")
      setRevisionCount(data.revision_count ?? 0)
      setLastRevisedItems(data.affected_items ?? [])
      closeApprovalModal()
    } catch (error) {
      console.error(error)
      window.alert(error instanceof Error ? error.message : "수정 요청 중 오류가 발생했습니다")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={styles.container}>
      <button className={styles.backBtn} onClick={onBack}>
        ← 뒤로
      </button>

      <h3 className={styles.title}>수정이 필요한 부분을 선택하세요</h3>

      <div className={styles.options}>
        {FEEDBACK_OPTIONS.map((option) => (
          <button
            key={option.value}
            className={`${styles.option} ${
              selectedFeedback?.value === option.value ? styles.selected : ""
            }`}
            onClick={() => setSelectedFeedback(option)}
            type="button"
          >
            {option.label}
          </button>
        ))}
      </div>

      {selectedFeedback ? (
        <div className={styles.feedbackInput}>
          <label className={styles.label}>
            추가 설명 {selectedFeedback.value === "custom" ? "*필수" : "(선택)"}
          </label>
          <textarea
            value={customFeedback}
            onChange={(event) => setCustomFeedback(event.target.value)}
            placeholder={selectedFeedback.promptHint ?? "구체적인 피드백을 입력해주세요"}
            rows={4}
            className={styles.textarea}
          />
          <small className={styles.counter}>{customFeedback.trim().length} / 10자 이상</small>
        </div>
      ) : null}

      <button
        className={styles.submitBtn}
        onClick={handleSubmit}
        disabled={!selectedFeedback || isSubmitting}
        type="button"
      >
        {isSubmitting ? "제출 중..." : "제출"}
      </button>
    </div>
  )
}
