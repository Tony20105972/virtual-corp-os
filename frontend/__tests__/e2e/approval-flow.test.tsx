// @ts-nocheck
import { fireEvent, render, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import MagicBar from "@/components/canvas/MagicBar"
import AIInterviewer from "@/components/canvas/AIInterviewer"
import { CEOBriefingPanel } from "@/components/approval/CEOBriefingPanel"
import { useInterviewStore } from "@/store/interviewStore"
import { useProjectStore } from "@/store/projectStore"

describe("Dynamic Interview And CEO Flow", () => {
  beforeEach(() => {
    useInterviewStore.getState().reset()
    useProjectStore.setState({
      projectId: null,
      prd_json: null,
      strategySummary: null,
      strategyReportReady: false,
      businessType: null,
      categoryTags: [],
      status: "intake_pending",
    })
  })

  it("shows freelancer/productivity saas questions before any CEO approval action", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => ({
          business_type: "saas",
          tags: ["freelancer", "productivity", "time-tracking"],
          questions: [
            {
              id: "target_user",
              type: "single_select_with_other",
              title: "가장 먼저 붙잡고 싶은 고객은 누구인가요?",
              options: [
                { value: "solo_freelancers", label: "혼자 일하는 프리랜서" },
                { value: "design_dev_freelancers", label: "디자이너/개발자 프리랜서" },
                { value: "other", label: "기타 직접 입력" },
              ],
            },
          ],
        }),
      }))
    )

    render(
      <>
        <MagicBar />
        <AIInterviewer />
        <CEOBriefingPanel />
      </>
    )

    fireEvent.change(screen.getByPlaceholderText("Describe your next company idea..."), {
      target: { value: "Time tracking tool for freelancers" },
    })
    fireEvent.click(screen.getByRole("button", { name: "↑" }))

    expect(await screen.findByText("가장 먼저 붙잡고 싶은 고객은 누구인가요?")).toBeInTheDocument()
    expect(screen.getByText("혼자 일하는 프리랜서")).toBeInTheDocument()
    expect(screen.queryByText("이 범위로 개발팀 착수")).not.toBeInTheDocument()
  })

  it("shows local booking questions for dog grooming service", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => ({
        ok: true,
        json: async () => ({
          business_type: "local_service",
          tags: ["local", "booking", "pet-care"],
          questions: [
            {
              id: "service_area",
              type: "single_select_with_other",
              title: "처음 집중할 운영 지역은 어디인가요?",
              options: [
                { value: "single_district", label: "한 개 구/동에 집중" },
                { value: "mobile_service", label: "출장형으로 이동 운영" },
                { value: "other", label: "기타 직접 입력" },
              ],
            },
            {
              id: "booking_flow",
              type: "single_select",
              title: "예약은 어떤 방식으로 받는 것이 가장 현실적인가요?",
              options: [{ value: "instant_booking", label: "실시간 예약" }],
            },
          ],
        }),
      }))
    )

    render(
      <>
        <MagicBar />
        <AIInterviewer />
      </>
    )

    fireEvent.change(screen.getByPlaceholderText("Describe your next company idea..."), {
      target: { value: "Local dog grooming booking service" },
    })
    fireEvent.click(screen.getByRole("button", { name: "↑" }))

    expect(await screen.findByText("처음 집중할 운영 지역은 어디인가요?")).toBeInTheDocument()
    fireEvent.click(screen.getByRole("button", { name: "한 개 구/동에 집중" }))
    fireEvent.click(screen.getByRole("button", { name: "Continue" }))
    expect(await screen.findByText("예약은 어떤 방식으로 받는 것이 가장 현실적인가요?")).toBeInTheDocument()
  })

  it("reveals CEO briefing actions only after strategy report is ready", async () => {
    useProjectStore.setState({
      status: "awaiting_ceo_approval",
      strategyReportReady: true,
      strategySummary: {
        headline: "프리랜서를 위한 타임 트래킹 SaaS",
        narrative: "초기 고객군을 프리랜서로 좁혀야 수요와 전환 포인트가 명확해집니다.",
        target_customer: "월별 청구와 프로젝트 관리가 동시에 필요한 프리랜서",
        value_proposition: "기록 누락 없이 청구 가능한 시간을 자동 정리합니다.",
        revenue_model: "월 구독 기반 Pro 플랜",
        mvp_scope: ["자동 타이머", "프로젝트별 리포트", "인보이스 초안"],
      },
    })

    render(<CEOBriefingPanel />)

    expect(screen.getByText("프리랜서를 위한 타임 트래킹 SaaS")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "이 범위로 개발팀 착수" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "전략 수정 요청" })).toBeInTheDocument()
  })

  it("does not crash when strategy summary is undefined", () => {
    useProjectStore.setState({
      status: "awaiting_ceo_approval",
      strategyReportReady: true,
      strategySummary: null,
    })

    render(<CEOBriefingPanel />)

    expect(screen.getByText("전략 핵심 요약을 정리 중입니다.")).toBeInTheDocument()
    expect(screen.getByText("추천 MVP 범위를 정리 중입니다.")).toBeInTheDocument()
  })

  it("shows empty state when mvp scope is missing or empty", () => {
    useProjectStore.setState({
      status: "awaiting_ceo_approval",
      strategyReportReady: true,
      strategySummary: {
        headline: "로컬 서비스 전략 보고",
        narrative: "핵심 구조는 잡혔지만 세부 MVP는 보강이 필요합니다.",
        mvp_scope: [],
      },
    })

    render(<CEOBriefingPanel />)

    expect(screen.getByText("추천 MVP 범위를 정리 중입니다.")).toBeInTheDocument()
  })

  it("renders populated mvp scope safely", () => {
    useProjectStore.setState({
      status: "awaiting_ceo_approval",
      strategyReportReady: true,
      strategySummary: {
        headline: "북클럽 커뮤니티 MVP",
        narrative: "초기 참여 루프가 명확한 커뮤니티 구조입니다.",
        mvp_scope: ["회원가입", "토론방", "월간 추천도서"],
      },
    })

    render(<CEOBriefingPanel />)

    expect(screen.getByText("회원가입")).toBeInTheDocument()
    expect(screen.getByText("토론방")).toBeInTheDocument()
    expect(screen.getByText("월간 추천도서")).toBeInTheDocument()
  })

  it("shows in-progress state while strategy report is not ready", () => {
    useProjectStore.setState({
      status: "strategy_running",
      strategyReportReady: false,
      strategySummary: null,
    })

    render(<CEOBriefingPanel />)

    expect(screen.getByText("Alex가 전략 보고서를 정리 중입니다.")).toBeInTheDocument()
    expect(screen.getByText(/전략 보고서가 아직 완전히 준비되지 않았습니다/)).toBeInTheDocument()
  })
})
