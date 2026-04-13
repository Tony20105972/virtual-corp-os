from typing import Literal, Optional
from typing_extensions import TypedDict


QuestionType = Literal["single_select", "single_select_with_other", "short_text"]
BusinessType = Literal["saas", "ecommerce", "local_service", "content_community", "marketplace", "general"]


class InterviewQuestionOption(TypedDict):
    value: str
    label: str


class InterviewQuestion(TypedDict, total=False):
    id: str
    type: QuestionType
    title: str
    description: Optional[str]
    options: list[InterviewQuestionOption]
    placeholder: Optional[str]


class InterviewPlan(TypedDict):
    business_type: BusinessType
    tags: list[str]
    questions: list[InterviewQuestion]


class InterviewAnswer(TypedDict, total=False):
    id: str
    title: str
    type: QuestionType
    answer: str
    selected_option: Optional[str]
