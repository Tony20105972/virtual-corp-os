"use client"

import { useEffect, useState } from "react"
import { createPortal } from "react-dom"
import { AnimatePresence, motion } from "framer-motion"
import { useProjectStore } from "@/store/projectStore"
import { ModalContent } from "./ModalContent"
import styles from "./styles.module.css"

export default function CanvasModal() {
  const canvasModalOpen = useProjectStore((s) => s.canvasModalOpen)
  const closeCanvasModal = useProjectStore((s) => s.closeCanvasModal)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (!canvasModalOpen) return

    const handleEsc = (event: KeyboardEvent) => {
      if (event.key === "Escape") closeCanvasModal()
    }

    window.addEventListener("keydown", handleEsc)
    return () => window.removeEventListener("keydown", handleEsc)
  }, [canvasModalOpen, closeCanvasModal])

  useEffect(() => {
    if (!mounted) return

    const previousOverflow = document.body.style.overflow
    if (canvasModalOpen) document.body.style.overflow = "hidden"

    return () => {
      document.body.style.overflow = previousOverflow
    }
  }, [canvasModalOpen, mounted])

  if (!mounted) return null

  return createPortal(
    <AnimatePresence>
      {canvasModalOpen ? (
        <div className={styles.portalRoot}>
          <motion.button
            type="button"
            className={styles.backdrop}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={closeCanvasModal}
            aria-label="전략 캔버스 닫기"
          />

          <motion.section
            className={styles.modal}
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3, ease: [0.4, 0, 0.2, 1] }}
            role="dialog"
            aria-modal="true"
            aria-labelledby="canvas-modal-title"
          >
            <ModalContent />
          </motion.section>
        </div>
      ) : null}
    </AnimatePresence>,
    document.body
  )
}
