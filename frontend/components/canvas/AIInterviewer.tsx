"use client"

import { useEffect, useMemo, useState } from "react"
import { useInterviewStore } from "@/store/interviewStore"
import { useProjectStore } from "@/store/projectStore"
import {
  BOARDROOM_QUESTIONS,
  composeStrategyAnswer,
  ETC_OPTION_VALUE,
} from "@/lib/strategy/questions"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

const TRANSITIONS = [
  "Assembling your boardroom...",
  "Alex is drafting the strategy memo...",
  "Your virtual company is moving into execution...",
]

interface StrategySelection {
  selectedOption: string
  etcText: string
}

function DotIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div style={{ display: "flex", gap: 8, marginBottom: 18 }}>
      {Array.from({ length: total }).map((_, index) => (
        <div
          key={index}
          style={{
            width: 30,
            height: 3,
            borderRadius: 999,
            background:
              index <= current ? "linear-gradient(90deg, var(--blue), #60a5fa)" : "rgba(255,255,255,0.12)",
            transition: "background 0.25s ease",
          }}
        />
      ))}
    </div>
  )
}

export default function AIInterviewer() {
  const { status, questions, answers, currentQ, idea, addAnswer, nextQuestion, setStatus } =
    useInterviewStore()
  const setProjectId = useProjectStore((s) => s.setProjectId)
  const setPrdJson = useProjectStore((s) => s.setPrdJson)

  const [transitionMsg, setTransitionMsg] = useState("")
  const [selections, setSelections] = useState<Record<string, StrategySelection>>({})

  const currentPrompt = questions[currentQ]
  const currentQuestion = useMemo(() => BOARDROOM_QUESTIONS[currentQ], [currentQ])
  const currentSelection = currentQuestion
    ? selections[currentQuestion.id] ?? { selectedOption: "", etcText: "" }
    : { selectedOption: "", etcText: "" }

  useEffect(() => {
    if (status !== "questioning") return

    setSelections((prev) => {
      const next = { ...prev }
      for (const question of BOARDROOM_QUESTIONS) {
        if (!next[question.id]) {
          next[question.id] = { selectedOption: "", etcText: "" }
        }
      }
      return next
    })
  }, [status])

  const updateSelection = (patch: Partial<StrategySelection>) => {
    if (!currentQuestion) return

    setSelections((prev) => ({
      ...prev,
      [currentQuestion.id]: {
        selectedOption: currentSelection.selectedOption,
        etcText: currentSelection.etcText,
        ...patch,
      },
    }))
  }

  const handleAnswer = async () => {
    if (!currentQuestion) return

    const option = currentQuestion.options.find(
      (item) => item.value === currentSelection.selectedOption
    )

    if (!option) return
    if (option.value === ETC_OPTION_VALUE && !currentSelection.etcText.trim()) return

    const answerText = composeStrategyAnswer(option.label, currentSelection.etcText)
    addAnswer(answerText)

    if (currentQ < BOARDROOM_QUESTIONS.length - 1) {
      nextQuestion()
      return
    }

    const msg = TRANSITIONS[Math.floor(Math.random() * TRANSITIONS.length)]
    setTransitionMsg(msg)
    setStatus("assembling")

    try {
      const allAnswers = [...answers, answerText].map((answer, index) => ({
        q: questions[index] ?? BOARDROOM_QUESTIONS[index]?.prompt ?? `Question ${index + 1}`,
        a: answer,
      }))

      const res = await fetch(`${API_URL}/run`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ idea, interview_answers: allAnswers }),
      })
      const data = await res.json()
      setProjectId(data.project_id)
      setPrdJson(data.prd_json ?? null)
      setStatus("done")
    } catch (err) {
      console.error("[AIInterviewer] /run 실패:", err)
      setStatus("done")
    }
  }

  if (status === "idle" || status === "done") return null

  if (status === "loading") {
    return (
      <div style={overlayStyle}>
        <div style={interviewerShellStyle}>
          <div style={eyebrowStyle}>Boardroom Intake</div>
          <div style={titleStyle}>Alex is preparing your strategy brief.</div>
          <div style={supportStyle}>Pulling the first questions into the room now.</div>
        </div>
      </div>
    )
  }

  if (status === "assembling") {
    return (
      <div style={overlayStyle}>
        <div style={interviewerShellStyle}>
          <div style={eyebrowStyle}>Company In Motion</div>
          <div style={titleStyle}>{transitionMsg}</div>
          <div style={supportStyle}>Strategy, PRD, and execution canvas are syncing.</div>
        </div>
      </div>
    )
  }

  if (!currentQuestion) return null

  return (
    <div style={overlayStyle}>
      <div style={interviewerShellStyle}>
        <div style={{ display: "flex", alignItems: "flex-start", gap: 12, marginBottom: 18 }}>
          <div
            style={{
              width: 42,
              height: 42,
              borderRadius: "50%",
              border: "1px solid rgba(96,165,250,0.34)",
              background: "rgba(59,130,246,0.12)",
              color: "var(--blue)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontFamily: "'DM Mono', monospace",
              fontSize: 14,
            }}
          >
            A
          </div>
          <div style={{ flex: 1 }}>
            <div style={eyebrowStyle}>Alex · Strategy Consultant</div>
            <div style={titleStyle}>{currentPrompt}</div>
            <div style={supportStyle}>Fast decisions only. Pick one direction and keep moving.</div>
          </div>
        </div>

        <DotIndicator current={currentQ} total={BOARDROOM_QUESTIONS.length} />

        <div
          role="radiogroup"
          aria-label={currentPrompt}
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))",
            gap: 10,
          }}
        >
          {currentQuestion.options.map((option) => {
            const selected = currentSelection.selectedOption === option.value
            return (
              <button
                key={option.value}
                type="button"
                onClick={() =>
                  updateSelection({
                    selectedOption: option.value,
                    etcText: option.value === ETC_OPTION_VALUE ? currentSelection.etcText : "",
                  })
                }
                style={{
                  border: selected
                    ? "1px solid rgba(96,165,250,0.45)"
                    : "1px solid rgba(255,255,255,0.08)",
                  background: selected ? "rgba(59,130,246,0.18)" : "rgba(255,255,255,0.03)",
                  color: selected ? "#eff6ff" : "#cbd5e1",
                  borderRadius: 16,
                  padding: "14px 14px",
                  textAlign: "left",
                  cursor: "pointer",
                  fontFamily: "'Pretendard', sans-serif",
                  fontSize: 14,
                  lineHeight: 1.3,
                  transition: "all 0.2s ease",
                }}
              >
                {option.label}
              </button>
            )
          })}
        </div>

        {currentSelection.selectedOption === ETC_OPTION_VALUE ? (
          <input
            value={currentSelection.etcText}
            onChange={(event) => updateSelection({ etcText: event.target.value })}
            onKeyDown={(event) => {
              if (event.key === "Enter") {
                event.preventDefault()
                void handleAnswer()
              }
            }}
            placeholder="Add your own direction"
            autoFocus
            style={etcInputStyle}
          />
        ) : null}

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 12,
            marginTop: 18,
          }}
        >
          <div style={footerHintStyle}>
            {currentQ + 1} of {BOARDROOM_QUESTIONS.length} strategic decisions
          </div>
          <button
            type="button"
            onClick={() => void handleAnswer()}
            disabled={
              !currentSelection.selectedOption ||
              (currentSelection.selectedOption === ETC_OPTION_VALUE &&
                !currentSelection.etcText.trim())
            }
            style={{
              border: "none",
              borderRadius: 999,
              padding: "12px 18px",
              background: "linear-gradient(135deg, var(--blue), #60a5fa)",
              color: "#eff6ff",
              fontFamily: "'DM Mono', monospace",
              fontSize: 12,
              letterSpacing: "0.08em",
              textTransform: "uppercase",
              cursor: "pointer",
              opacity:
                !currentSelection.selectedOption ||
                (currentSelection.selectedOption === ETC_OPTION_VALUE &&
                  !currentSelection.etcText.trim())
                  ? 0.45
                  : 1,
            }}
          >
            {currentQ === BOARDROOM_QUESTIONS.length - 1 ? "Assemble Company" : "Continue"}
          </button>
        </div>
      </div>
    </div>
  )
}

const overlayStyle: React.CSSProperties = {
  position: "absolute",
  inset: 0,
  zIndex: 6,
  display: "grid",
  placeItems: "center",
  padding: "24px",
  pointerEvents: "none",
}

const interviewerShellStyle: React.CSSProperties = {
  width: "min(760px, calc(100vw - 28px))",
  borderRadius: 28,
  border: "1px solid rgba(255,255,255,0.1)",
  background: "rgba(8, 13, 24, 0.82)",
  backdropFilter: "blur(18px)",
  boxShadow: "0 30px 70px rgba(0,0,0,0.3)",
  padding: "24px 24px 22px",
  boxSizing: "border-box",
  pointerEvents: "auto",
}

const eyebrowStyle: React.CSSProperties = {
  fontFamily: "'DM Mono', monospace",
  fontSize: 11,
  letterSpacing: "0.16em",
  textTransform: "uppercase",
  color: "rgba(148, 163, 184, 0.82)",
}

const titleStyle: React.CSSProperties = {
  marginTop: 8,
  fontFamily: "'Syne', sans-serif",
  fontSize: "clamp(1.5rem, 3vw, 2.2rem)",
  lineHeight: 1.02,
  letterSpacing: "-0.05em",
  color: "#f8fafc",
}

const supportStyle: React.CSSProperties = {
  marginTop: 10,
  fontFamily: "'Pretendard', sans-serif",
  fontSize: 14,
  lineHeight: 1.7,
  color: "rgba(203, 213, 225, 0.8)",
}

const etcInputStyle: React.CSSProperties = {
  width: "100%",
  marginTop: 14,
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 16,
  background: "rgba(255,255,255,0.04)",
  color: "#e2e8f0",
  padding: "14px 16px",
  fontFamily: "'Pretendard', sans-serif",
  fontSize: 14,
  outline: "none",
  boxSizing: "border-box",
}

const footerHintStyle: React.CSSProperties = {
  fontFamily: "'DM Mono', monospace",
  fontSize: 11,
  letterSpacing: "0.08em",
  textTransform: "uppercase",
  color: "rgba(148, 163, 184, 0.82)",
}
