import type { InterviewAnswer, InterviewQuestion } from "@/types/interview"

export const OTHER_OPTION_VALUE = "other"

export function buildAnswerPayload(
  question: InterviewQuestion,
  selection: { selectedOption: string; etcText: string; shortText: string }
): InterviewAnswer {
  if (question.type === "short_text") {
    return {
      id: question.id,
      title: question.title,
      type: question.type,
      answer: selection.shortText.trim(),
      selected_option: null,
    }
  }

  const selected = question.options?.find((option) => option.value === selection.selectedOption)
  const optionLabel = selected?.label ?? ""
  const answer =
    selection.selectedOption === OTHER_OPTION_VALUE
      ? selection.etcText.trim()
      : optionLabel

  return {
    id: question.id,
    title: question.title,
    type: question.type,
    answer,
    selected_option: selection.selectedOption,
  }
}

export function isQuestionAnswered(
  question: InterviewQuestion,
  selection: { selectedOption: string; etcText: string; shortText: string }
) {
  if (question.type === "short_text") {
    return selection.shortText.trim().length > 1
  }
  if (!selection.selectedOption) return false
  if (question.type === "single_select_with_other" && selection.selectedOption === OTHER_OPTION_VALUE) {
    return selection.etcText.trim().length > 1
  }
  return true
}
