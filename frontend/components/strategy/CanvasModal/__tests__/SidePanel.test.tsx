// @ts-nocheck
import { fireEvent, render, screen } from "@testing-library/react"
import { beforeEach, describe, expect, it } from "vitest"
import { SidePanel } from "../SidePanel"
import { useProjectStore } from "@/store/projectStore"

describe("SidePanel", () => {
  beforeEach(() => {
    useProjectStore.setState({
      prd_json: {
        VP: "가치 제안 전문",
        CS: "고객 세그먼트",
        CH: "채널",
        CR: "고객 관계",
        "R$": "수익원",
        KR: "핵심 자원",
        KA: "핵심 활동",
        KP: "핵심 파트너",
        "C$": "비용 구조",
      },
      selectedCanvasNode: "VP",
    })
  })

  it("slides in when a node is selected", () => {
    render(<SidePanel />)
    expect(screen.getByTestId("side-panel")).toBeInTheDocument()
    expect(screen.getByText("가치 제안")).toBeInTheDocument()
    expect(screen.getByText("가치 제안 전문")).toBeInTheDocument()
  })

  it("closes when back button is clicked", () => {
    render(<SidePanel />)
    fireEvent.click(screen.getByRole("button", { name: "← 뒤로" }))
    expect(useProjectStore.getState().selectedCanvasNode).toBeNull()
  })
})
