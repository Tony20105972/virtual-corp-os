// @ts-nocheck
import { fireEvent, render, screen } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"
import { CanvasNode } from "../CanvasNode"
import { CANVAS_NODES } from "@/lib/canvas/canvasConfig"
import { useProjectStore } from "@/store/projectStore"

describe("CanvasNode", () => {
  beforeEach(() => {
    useProjectStore.setState({ selectedCanvasNode: null })
  })

  it("renders content", () => {
    render(
      <CanvasNode
        config={CANVAS_NODES.VP}
        content="테스트 가치 제안"
        isSelected={false}
        delay={0}
      />
    )

    expect(screen.getByText("가치 제안")).toBeInTheDocument()
    expect(screen.getByText("테스트 가치 제안")).toBeInTheDocument()
  })

  it("applies selected state styling", () => {
    render(
      <CanvasNode
        config={CANVAS_NODES.VP}
        content="테스트 가치 제안"
        isSelected
        delay={0}
      />
    )

    expect(screen.getByTestId("selected-indicator-VP")).toBeInTheDocument()
  })

  it("truncates content longer than 60 characters", () => {
    const longContent = "A".repeat(100)
    render(
      <CanvasNode
        config={CANVAS_NODES.VP}
        content={longContent}
        isSelected={false}
        delay={0}
      />
    )

    expect(screen.getByText(`${"A".repeat(60)}...`)).toBeInTheDocument()
  })

  it("handles click interaction", () => {
    const spy = vi.spyOn(useProjectStore.getState(), "selectCanvasNode")
    render(
      <CanvasNode
        config={CANVAS_NODES.VP}
        content="테스트 가치 제안"
        isSelected={false}
        delay={0}
      />
    )

    fireEvent.click(screen.getByTestId("canvas-node-VP"))
    expect(spy).toHaveBeenCalledWith("VP")
    spy.mockRestore()
  })
})
