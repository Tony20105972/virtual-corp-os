"use client"

import { useEffect, useState } from "react"
import { createPortal } from "react-dom"
import { useProjectStore } from "@/store/projectStore"
import { useApprovalApi } from "@/hooks/useApprovalApi"
import styles from "./PaymentConfirmModal.module.css"

export function PaymentConfirmModal() {
  const paymentConfirmModalOpen = useProjectStore((state) => state.paymentConfirmModalOpen)
  const closePaymentConfirmModal = useProjectStore((state) => state.closePaymentConfirmModal)
  const projectId = useProjectStore((state) => state.projectId)
  const setStatus = useProjectStore((state) => state.setStatus)
  const api = useApprovalApi()

  const [mounted, setMounted] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!paymentConfirmModalOpen) return
    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === "Escape" && !isProcessing) closePaymentConfirmModal()
    }
    window.addEventListener("keydown", handleEsc)
    return () => window.removeEventListener("keydown", handleEsc)
  }, [closePaymentConfirmModal, isProcessing, paymentConfirmModalOpen])

  const handleConfirm = async () => {
    if (!projectId) return

    setIsProcessing(true)
    try {
      const paymentIntentId = "pi_mock_123"
      await api.confirmPayment(projectId, paymentIntentId)
      setStatus("deploying")
      closePaymentConfirmModal()
    } catch (error) {
      console.error(error)
      window.alert("결제 확인 중 오류가 발생했습니다")
    } finally {
      setIsProcessing(false)
    }
  }

  const handleCancel = () => {
    closePaymentConfirmModal()
  }

  if (!mounted || !paymentConfirmModalOpen) return null

  return createPortal(
    <div className={styles.backdrop}>
      <div className={styles.modal} role="dialog" aria-modal="true" aria-labelledby="payment-modal-title">
        <h2 id="payment-modal-title" className={styles.title}>
          결제 확인
        </h2>
        <p className={styles.description}>
          개발을 시작하시면 <strong>$29</strong>가 청구됩니다.
        </p>
        <p className={styles.description}>계속하시겠습니까?</p>

        <div className={styles.actions}>
          <button className={styles.cancelBtn} onClick={handleCancel} disabled={isProcessing}>
            취소
          </button>
          <button className={styles.confirmBtn} onClick={handleConfirm} disabled={isProcessing}>
            {isProcessing ? "처리 중..." : "확인 및 결제"}
          </button>
        </div>
      </div>
    </div>,
    document.body
  )
}
