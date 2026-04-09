"use client"

import { useState, useEffect } from "react"
import { useInterviewStore }   from "@/store/interviewStore"
import { useProjectStore }     from "@/store/projectStore"
import { useTypewriter }       from "@/hooks/useTypewriter"

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

const REACTIONS   = ["Interesting. One more thing—", "Got it. Last question—"]
const TRANSITIONS = [
  "Assembling your team...",
  "Alex is reviewing your brief...",
  "Your virtual corp is coming online...",
]

function DotIndicator({ current, total }: { current: number; total: number }) {
  return (
    <div style={{ display: "flex", gap: 6, justifyContent: "center", marginBottom: 16 }}>
      {Array.from({ length: total }).map((_, i) => (
        <div
          key={i}
          style={{
            width:      8,
            height:     8,
            borderRadius: "50%",
            background: i <= current ? "var(--blue)" : "rgba(255,255,255,0.15)",
            transition: "background 0.3s",
          }}
        />
      ))}
    </div>
  )
}

export default function AIInterviewer() {
  const {
    status, questions, answers, currentQ, idea,
    addAnswer, nextQuestion, setStatus,
  } = useInterviewStore()

  const setProjectId = useProjectStore((s) => s.setProjectId)
  const setPrdJson = useProjectStore((s) => s.setPrdJson)

  const [answerInput,   setAnswerInput]   = useState("")
  const [showReaction,  setShowReaction]  = useState(false)
  const [reactionText,  setReactionText]  = useState("")
  const [questionText,  setQuestionText]  = useState("")
  const [transitionMsg, setTransitionMsg] = useState("")

  // 질문 전환 처리 — Q2/Q3 진입 시 맥락 반응 먼저 표시
  useEffect(() => {
    if (status === "questioning" && questions[currentQ]) {
      setAnswerInput("")
      setShowReaction(false)

      if (currentQ > 0) {
        setReactionText(REACTIONS[currentQ - 1])
        setShowReaction(true)
        const t = setTimeout(() => {
          setShowReaction(false)
          setQuestionText(questions[currentQ])
        }, 1200)
        return () => clearTimeout(t)
      } else {
        setQuestionText(questions[currentQ])
      }
    }
  }, [currentQ, status, questions])

  const { displayed: typedQuestion, done: questionDone } = useTypewriter(questionText, 30)

  const handleAnswer = async () => {
    const trimmed = answerInput.trim()
    // 타이핑 완료 전 Enter 씹기
    if (!trimmed || !questionDone) return

    addAnswer(trimmed)
    setAnswerInput("")

    if (currentQ < 2) {
      nextQuestion()
    } else {
      // 3문 완료 — 트랜지션 + /run 호출
      const msg = TRANSITIONS[Math.floor(Math.random() * TRANSITIONS.length)]
      setTransitionMsg(msg)
      setStatus("assembling")

      try {
        const allAnswers = [...answers, trimmed].map((a, i) => ({
          q: questions[i],
          a,
        }))
        const res = await fetch(`${API_URL}/run`, {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body:    JSON.stringify({ idea, interview_answers: allAnswers }),
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
  }

  if (status === "idle" || status === "done") return null

  if (status === "loading") {
    return (
      <div style={overlayStyle}>
        <div style={{ color: "var(--blue)", fontFamily: "'DM Mono', monospace", fontSize: 13 }}>
          Alex is preparing your questions...
        </div>
      </div>
    )
  }

  if (status === "assembling") {
    return (
      <div style={overlayStyle}>
        <div style={{ color: "#F8FAFC", fontFamily: "'Syne', sans-serif", fontSize: 16, fontWeight: 700 }}>
          {transitionMsg}
        </div>
      </div>
    )
  }

  return (
    <div style={overlayStyle}>
      {/* Alex 헤더 */}
      <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
        <div style={{
          width: 28, height: 28, borderRadius: "50%",
          background: "rgba(59,130,246,0.2)",
          border: "1px solid var(--blue)",
          display: "flex", alignItems: "center", justifyContent: "center",
          fontSize: 12, color: "var(--blue)", fontWeight: 700,
        }}>
          A
        </div>
        <span style={{ fontFamily: "'Syne', sans-serif", fontSize: 13, fontWeight: 700, color: "#F8FAFC" }}>
          Alex
        </span>
        <span style={{
          fontFamily: "'DM Mono', monospace", fontSize: 10,
          color: "var(--slate-d)", marginLeft: "auto",
        }}>
          Strategy Consultant
        </span>
      </div>

      {/* 도트 인디케이터 */}
      <DotIndicator current={currentQ} total={3} />

      {/* 맥락 반응 */}
      {showReaction && (
        <div style={{
          fontSize: 12, color: "var(--slate)", fontStyle: "italic", marginBottom: 8,
        }}>
          {reactionText}
        </div>
      )}

      {/* 타이핑 질문 */}
      {!showReaction && (
        <div style={{
          fontFamily: "'Pretendard', sans-serif",
          fontSize: 15, fontWeight: 600, color: "#F8FAFC",
          marginBottom: 16, minHeight: 48, lineHeight: 1.6,
        }}>
          {typedQuestion}
          {!questionDone && (
            <span style={{ opacity: 0.5 }}>|</span>
          )}
        </div>
      )}

      {/* 답변 입력 — 타이핑 완료 후만 노출 */}
      {questionDone && !showReaction && (
        <>
          <textarea
            value={answerInput}
            onChange={(e) => setAnswerInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault()
                handleAnswer()
              }
            }}
            placeholder="Your answer... (Enter to continue)"
            rows={2}
            autoFocus
            style={{
              width:      "100%",
              background: "rgba(255,255,255,0.05)",
              border:     "1px solid rgba(255,255,255,0.1)",
              borderRadius: 8,
              color:      "#E2E8F0",
              fontSize:   13,
              padding:    "10px 12px",
              fontFamily: "'Pretendard', sans-serif",
              resize:     "none",
              outline:    "none",
              boxSizing:  "border-box",
            }}
          />
          <div style={{
            fontSize: 10, color: "var(--slate-d)", marginTop: 6,
            fontFamily: "'DM Mono', monospace",
          }}>
            Enter to continue · Shift+Enter for new line
          </div>
        </>
      )}
    </div>
  )
}

const overlayStyle: React.CSSProperties = {
  position:       "absolute",
  bottom:         90,
  left:           "50%",
  transform:      "translateX(-50%)",
  width:          "min(480px, calc(100vw - 48px))",
  zIndex:         20,
  background:     "rgba(10, 15, 30, 0.95)",
  backdropFilter: "blur(16px)",
  border:         "1px solid rgba(255,255,255,0.1)",
  borderRadius:   14,
  padding:        "20px 22px",
}
