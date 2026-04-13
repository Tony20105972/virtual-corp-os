export type QuestionType = "single_select" | "single_select_with_other" | "short_text"

export type InterviewQuestionOption = {
  value: string
  label: string
}

export type InterviewQuestion = {
  id: string
  type: QuestionType
  title: string
  description?: string
  options?: InterviewQuestionOption[]
  placeholder?: string
}

export type InterviewPlan = {
  business_type: string
  tags: string[]
  questions: InterviewQuestion[]
}

export type InterviewAnswer = {
  id: string
  title: string
  type: QuestionType
  answer: string
  selected_option?: string | null
}
