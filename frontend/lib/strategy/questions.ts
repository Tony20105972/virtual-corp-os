export interface StrategyQuestionOption {
  value: string
  label: string
}

export interface StrategyQuestion {
  id: string
  prompt: string
  options: StrategyQuestionOption[]
}

export const ETC_OPTION_VALUE = "etc"

export const BOARDROOM_QUESTIONS: StrategyQuestion[] = [
  {
    id: "business-type",
    prompt: "What type of business is this?",
    options: [
      { value: "saas", label: "SaaS" },
      { value: "marketplace", label: "Marketplace" },
      { value: "ecommerce", label: "E-commerce" },
      { value: "service", label: "Service" },
      { value: "content", label: "Content" },
      { value: ETC_OPTION_VALUE, label: "ETC" },
    ],
  },
  {
    id: "primary-customer",
    prompt: "Who is your primary customer?",
    options: [
      { value: "students", label: "Students" },
      { value: "professionals", label: "Professionals" },
      { value: "startups", label: "Startups" },
      { value: "smb", label: "SMB" },
      { value: "enterprise", label: "Enterprise" },
      { value: ETC_OPTION_VALUE, label: "ETC" },
    ],
  },
  {
    id: "main-goal",
    prompt: "What is your main goal?",
    options: [
      { value: "validate-idea", label: "Validate idea" },
      { value: "get-users", label: "Get users" },
      { value: "generate-revenue", label: "Generate revenue" },
      { value: "build-mvp", label: "Build MVP" },
      { value: "landing-page", label: "Landing page" },
      { value: ETC_OPTION_VALUE, label: "ETC" },
    ],
  },
  {
    id: "core-value",
    prompt: "What is your core value?",
    options: [
      { value: "save-time", label: "Save time" },
      { value: "make-money", label: "Make money" },
      { value: "reduce-cost", label: "Reduce cost" },
      { value: "better-ux", label: "Better UX" },
      { value: "automation", label: "Automation" },
      { value: ETC_OPTION_VALUE, label: "ETC" },
    ],
  },
  {
    id: "ai-priority",
    prompt: "What should AI build first?",
    options: [
      { value: "strategy", label: "Strategy" },
      { value: "landing-page", label: "Landing page" },
      { value: "payment-system", label: "Payment system" },
      { value: "onboarding", label: "Onboarding" },
      { value: "marketing", label: "Marketing" },
      { value: ETC_OPTION_VALUE, label: "ETC" },
    ],
  },
]

export function composeStrategyAnswer(selectedLabel: string, etcText?: string) {
  if (!etcText?.trim()) return selectedLabel
  return `${selectedLabel}: ${etcText.trim()}`
}
