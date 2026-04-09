// @ts-nocheck
import { fireEvent, render, screen, within } from "@testing-library/react"
import { beforeEach, describe, expect, it } from "vitest"
import CanvasModal from ".."
import { useProjectStore } from "@/store/projectStore"

describe("Canvas modal full flow", () => {
  beforeEach(() => {
    useProjectStore.setState({
      canvasModalOpen: true,
      selectedCanvasNode: null,
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
    })
  })

  it("opens, selects a node, shows detail, and closes on approval", async () => {
    render(<CanvasModal />)

    expect(await screen.findByRole("dialog")).toBeInTheDocument()
    fireEvent.click(screen.getByTestId("canvas-node-VP"))
    const sidePanel = await screen.findByTestId("side-panel")
    expect(sidePanel).toBeInTheDocument()
    expect(within(sidePanel).getByText("가치 제안 전문")).toBeInTheDocument()

    fireEvent.click(screen.getByRole("button", { name: "승인 진행 →" }))
    expect(useProjectStore.getState().canvasModalOpen).toBe(false)
  })
})
