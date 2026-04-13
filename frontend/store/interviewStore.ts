import { create } from "zustand"
import type { InterviewAnswer, InterviewQuestion } from "@/types/interview"

export type InterviewStatus =
  | "idle"        // Magic Bar 노출
  | "loading"     // 질문 생성 중
  | "questioning" // 인터뷰 진행 중
  | "strategy_running"
  | "done"        // SSE 연결 완료

interface InterviewStore {
  status:    InterviewStatus
  idea:      string
  businessType: string | null
  tags: string[]
  questions: InterviewQuestion[]
  answers:   InterviewAnswer[]
  currentQ:  number

  setIdea:      (idea: string) => void
  setPlan:      (plan: { business_type: string; tags: string[]; questions: InterviewQuestion[] }) => void
  addAnswer:    (a: InterviewAnswer) => void
  nextQuestion: () => void
  setStatus:    (s: InterviewStatus) => void
  reset:        () => void
}

export const useInterviewStore = create<InterviewStore>((set, get) => ({
  status:    "idle",
  idea:      "",
  businessType: null,
  tags: [],
  questions: [],
  answers:   [],
  currentQ:  0,

  setIdea:      (idea) => set({ idea }),
  setPlan:      (plan)   =>
    set({
      businessType: plan.business_type,
      tags: plan.tags,
      questions: plan.questions,
      answers: [],
      status: "questioning",
      currentQ: 0,
    }),
  addAnswer:    (a)    => set((s) => ({ answers: [...s.answers, a] })),
  nextQuestion: ()     => set((s) => ({ currentQ: s.currentQ + 1 })),
  setStatus:    (s)    => set({ status: s }),
  reset: () => set({
    status: "idle",
    idea: "",
    businessType: null,
    tags: [],
    questions: [],
    answers: [],
    currentQ: 0,
  }),
}))
