"use client"

import { useEffect, useState } from "react"
import { createPortal } from "react-dom"
import { useProjectStore } from "@/store/projectStore"
import { useApprovalApi } from "@/hooks/useApprovalApi"
import { FeedbackSelector } from "./FeedbackSelector"
import styles from "./ApprovalModal.module.css"

export function ApprovalModal() {
  const approvalModalOpen = useProjectStore((state) => state.approvalModalOpen)
  const closeApprovalModal = useProjectStore((state) => state.closeApprovalModal)
  const openPaymentConfirmModal = useProjectStore((state) => state.openPaymentConfirmModal)
  const setStatus = useProjectStore((state) => state.setStatus)
  const projectId = useProjectStore((state) => state.projectId)
  const api = useApprovalApi()

  const [mounted, setMounted] = useState(false)
  const [showFeedback, setShowFeedback] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!approvalModalOpen) {
      setShowFeedback(false)
      return
    }

    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeApprovalModal()
    }

    window.addEventListener("keydown", handleEsc)
    return () => window.removeEventListener("keydown", handleEsc)
  }, [approvalModalOpen, closeApprovalModal])

  useEffect(() => {
    if (!mounted) return
    const previousOverflow = document.body.style.overflow
    if (approvalModalOpen) document.body.style.overflow = "hidden"
    return () => {
      document.body.style.overflow = previousOverflow
    }
  }, [approvalModalOpen, mounted])

  const handleApprove = async () => {
    if (!projectId || isSubmitting) return

    setIsSubmitting(true)
    try {
      await api.approveProject(projectId)
      setStatus("build_pending")
      closeApprovalModal()
      openPaymentConfirmModal()
    } catch (error) {
      console.error(error)
      window.alert("승인 처리 중 오류가 발생했습니다")
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!mounted || !approvalModalOpen) return null

  return createPortal(
    <div className={styles.backdrop} onClick={closeApprovalModal} role="presentation">
      <div
        className={styles.modal}
        onClick={(event) => event.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="approval-modal-title"
      >
        {!showFeedback ? (
          <>
            <h2 id="approval-modal-title" className={styles.title}>
              전략을 승인하시겠습니까?
            </h2>
            <p className={styles.description}>
              PRD 9개 항목 검토가 완료되었습니다. 승인 후 결제를 확인하면 개발이 시작됩니다.
            </p>

            <div className={styles.actions}>
              <button
                className={styles.reviseBtn}
                onClick={() => setShowFeedback(true)}
                disabled={isSubmitting}
              >
                전략 수정 요청
              </button>
              <button
                className={styles.approveBtn}
                onClick={handleApprove}
                disabled={isSubmitting}
              >
                {isSubmitting ? "처리 중..." : "승인하고 개발 시작"}
              </button>
            </div>
          </>
        ) : (
          <FeedbackSelector onBack={() => setShowFeedback(false)} />
        )}
      </div>
    </div>,
    document.body
  )
}
