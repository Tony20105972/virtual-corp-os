"use client"

import type { ProjectStatus } from "@/types/approval"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

export type ProjectStatusResponse = {
  project_id: string
  status: ProjectStatus
  raw_idea?: string
  business_type?: string
  category_tags?: string[]
  strategy_report_ready?: boolean
  strategy_summary?: {
    headline: string
    narrative: string
    target_customer: string
    value_proposition: string
    revenue_model: string
    mvp_scope: string[]
  } | null
  prd_json?: Record<string, string> | null
  revision_count: number
  last_revised_items: string[]
  updated_at?: string
  approval_requested_at?: string | null
}

export function useApprovalApi() {
  return {
    async getStatus(projectId: string): Promise<ProjectStatusResponse> {
      const res = await fetch(`${API_URL}/projects/${projectId}/status`)
      if (!res.ok) {
        const error = new Error("Status fetch failed")
        ;(error as Error & { status?: number }).status = res.status
        throw error
      }
      return res.json()
    },

    async approveProject(projectId: string) {
      const res = await fetch(`${API_URL}/projects/${projectId}/approve`, {
        method: "POST",
      })
      if (!res.ok) throw new Error("Approval failed")
      return res.json()
    },

    async requestRevision(
      projectId: string,
      payload: { feedback_option: string; custom_feedback: string | null }
    ) {
      const res = await fetch(`${API_URL}/projects/${projectId}/revise`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const error = await res.json().catch(() => null)
        throw new Error(error?.detail?.detail ?? error?.detail ?? "Revision failed")
      }
      return res.json()
    },

    async confirmPayment(projectId: string, stripe_payment_intent_id: string) {
      const res = await fetch(`${API_URL}/projects/${projectId}/confirm-payment`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ stripe_payment_intent_id }),
      })
      if (!res.ok) throw new Error("Payment confirmation failed")
      return res.json()
    },
  }
}
