// @ts-nocheck
import { fireEvent, render, screen } from "@testing-library/react"
import { beforeEach, describe, expect, it } from "vitest"
import { ActionButtons } from "../ActionButtons"
import { useProjectStore } from "@/store/projectStore"

describe("ActionButtons", () => {
  beforeEach(() => {
    useProjectStore.setState({
      canvasModalOpen: true,
    })
  })

  it("closes the modal on secondary action", () => {
    render(<ActionButtons />)
    fireEvent.click(screen.getByRole("button", { name: "닫기" }))
    expect(useProjectStore.getState().canvasModalOpen).toBe(false)
  })

  it("returns to briefing by closing the modal", () => {
    render(<ActionButtons />)
    fireEvent.click(screen.getByRole("button", { name: "CEO 브리핑으로 돌아가기" }))
    expect(useProjectStore.getState().canvasModalOpen).toBe(false)
  })
})
