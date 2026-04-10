import { create } from "zustand"

export type InterviewStatus =
  | "idle"        // Magic Bar 노출
  | "loading"     // 질문 생성 중
  | "questioning" // 인터뷰 진행 중
  | "assembling"  // /run 호출 중
  | "done"        // SSE 연결 완료

interface InterviewStore {
  status:    InterviewStatus
  idea:      string
  questions: string[]
  answers:   string[]
  currentQ:  number

  setIdea:      (idea: string) => void
  setQuestions: (qs: string[]) => void
  addAnswer:    (a: string) => void
  nextQuestion: () => void
  setStatus:    (s: InterviewStatus) => void
  reset:        () => void
}

export const useInterviewStore = create<InterviewStore>((set, get) => ({
  status:    "idle",
  idea:      "",
  questions: [],
  answers:   [],
  currentQ:  0,

  setIdea:      (idea) => set({ idea }),
  setQuestions: (qs)   =>
    set({ questions: qs, answers: [], status: "questioning", currentQ: 0 }),
  addAnswer:    (a)    => set((s) => ({ answers: [...s.answers, a] })),
  nextQuestion: ()     => set((s) => ({ currentQ: s.currentQ + 1 })),
  setStatus:    (s)    => set({ status: s }),
  reset: () => set({ status: "idle", idea: "", questions: [], answers: [], currentQ: 0 }),
}))
