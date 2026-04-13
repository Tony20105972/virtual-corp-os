import re

from schemas.interview import InterviewPlan, InterviewQuestion


BUSINESS_TYPE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("saas", ["saas", "software", "tool", "app", "platform", "dashboard", "crm", "automation", "tracking"]),
    ("ecommerce", ["shopify", "store", "ecommerce", "e-commerce", "commerce", "product", "selling", "merch", "case"]),
    ("local_service", ["booking", "reservation", "local", "nearby", "salon", "grooming", "cleaning", "clinic", "studio", "service"]),
    ("content_community", ["community", "content", "newsletter", "creator", "media", "membership", "audience", "forum", "course"]),
    ("marketplace", ["marketplace", "matching", "two-sided", "vendors", "buyers"]),
]

TAG_KEYWORDS: list[tuple[str, list[str]]] = [
    ("freelancer", ["freelancer", "freelance", "independent"]),
    ("productivity", ["productivity", "workflow", "efficiency", "time", "tracking"]),
    ("time-tracking", ["time tracking", "tracking", "timesheet"]),
    ("local", ["local", "nearby", "area", "district"]),
    ("booking", ["booking", "reservation", "schedule"]),
    ("pet-care", ["dog", "pet", "grooming"]),
    ("shopify", ["shopify"]),
    ("custom-products", ["custom", "personalized", "phone case", "cases"]),
    ("ecommerce", ["store", "product", "shopify", "commerce"]),
    ("content", ["content", "newsletter", "creator", "media"]),
    ("community", ["community", "membership", "forum"]),
]


def normalize_text(raw_idea: str) -> str:
    return re.sub(r"\s+", " ", raw_idea.lower()).strip()


def infer_business_type(raw_idea: str) -> str:
    normalized = normalize_text(raw_idea)
    scores: dict[str, int] = {}
    for business_type, keywords in BUSINESS_TYPE_KEYWORDS:
        scores[business_type] = sum(1 for keyword in keywords if keyword in normalized)
    best_type = max(scores, key=scores.get, default="general")
    return best_type if scores.get(best_type, 0) > 0 else "general"


def infer_tags(raw_idea: str) -> list[str]:
    normalized = normalize_text(raw_idea)
    tags = [tag for tag, keywords in TAG_KEYWORDS if any(keyword in normalized for keyword in keywords)]
    if not tags:
        tokens = [token for token in re.findall(r"[a-zA-Z][a-zA-Z-]+", normalized) if len(token) > 3]
        tags = tokens[:3]
    return tags[:4]


def option(value: str, label: str) -> dict[str, str]:
    return {"value": value, "label": label}


def build_saas_questions(tags: list[str]) -> list[InterviewQuestion]:
    freelancer = "freelancer" in tags
    productivity = "productivity" in tags or "time-tracking" in tags
    user_options = [
        option("solo_freelancers", "혼자 일하는 프리랜서"),
        option("small_agencies", "소규모 에이전시/스튜디오"),
        option("remote_teams", "원격 협업 팀"),
        option("ops_managers", "운영/프로젝트 매니저"),
        option("other", "기타 직접 입력"),
    ]
    problem_options = [
        option("time_logging", "작업 시간 기록이 누락되거나 귀찮다"),
        option("billing", "청구 가능한 시간과 금액 계산이 어렵다"),
        option("client_visibility", "클라이언트에게 진행 상황을 보여주기 어렵다"),
        option("workflow_chaos", "업무 흐름과 우선순위가 자주 꼬인다"),
        option("other", "기타 직접 입력"),
    ]
    if freelancer:
        user_options[1] = option("design_dev_freelancers", "디자이너/개발자 프리랜서")
    if productivity:
        problem_options[3] = option("focus_loss", "집중 시간이 끊기고 생산성이 떨어진다")

    return [
        {
            "id": "target_user",
            "type": "single_select_with_other",
            "title": "가장 먼저 붙잡고 싶은 고객은 누구인가요?",
            "description": "첫 100명의 고객을 떠올리며 골라주세요.",
            "options": user_options,
        },
        {
            "id": "core_problem",
            "type": "single_select_with_other",
            "title": "그 고객이 가장 자주 겪는 문제는 무엇인가요?",
            "options": problem_options,
        },
        {
            "id": "mvp_job",
            "type": "single_select",
            "title": "MVP가 가장 먼저 대신 해줘야 하는 일은 무엇인가요?",
            "options": [
                option("track_and_report", "기록과 리포트를 자동화한다"),
                option("organize_work", "업무 흐름과 우선순위를 정리한다"),
                option("client_update", "클라이언트 커뮤니케이션을 줄인다"),
                option("invoice", "청구/결제를 더 쉽게 만든다"),
            ],
        },
        {
            "id": "pricing_model",
            "type": "single_select",
            "title": "초기 가격 모델은 어떤 쪽이 현실적일까요?",
            "options": [
                option("monthly", "월 구독"),
                option("per_seat", "사용자 수 기준 과금"),
                option("usage", "사용량 기준 과금"),
                option("freemium", "무료 + 유료 전환"),
            ],
        },
        {
            "id": "current_alternative",
            "type": "short_text",
            "title": "지금 고객은 이 문제를 무엇으로 버티고 있나요?",
            "placeholder": "예: 엑셀, 노션, 토글, 카카오톡 수기 관리",
        },
    ]


def build_local_service_questions(tags: list[str]) -> list[InterviewQuestion]:
    pet_service = "pet-care" in tags
    return [
        {
            "id": "service_area",
            "type": "single_select_with_other",
            "title": "처음 집중할 운영 지역은 어디인가요?",
            "options": [
                option("single_district", "한 개 구/동에 집중"),
                option("two_districts", "인접 2개 지역"),
                option("citywide", "도시 전역"),
                option("mobile_service", "출장형으로 이동 운영"),
                option("other", "기타 직접 입력"),
            ],
        },
        {
            "id": "booking_flow",
            "type": "single_select",
            "title": "예약은 어떤 방식으로 받는 것이 가장 현실적인가요?",
            "options": [
                option("instant_booking", "실시간 예약"),
                option("request_then_confirm", "요청 후 수동 확정"),
                option("chat_first", "채팅 상담 후 예약"),
                option("phone_assisted", "전화/메시지 보조 예약"),
            ],
        },
        {
            "id": "operating_hours",
            "type": "single_select_with_other",
            "title": "운영 시간은 어떤 형태가 적합한가요?",
            "options": [
                option("weekday_daytime", "평일 주간"),
                option("evening_weekend", "퇴근 후/주말 중심"),
                option("appointment_only", "예약 건에만 맞춰 유동 운영"),
                option("full_day", "상시 운영"),
                option("other", "기타 직접 입력"),
            ],
        },
        {
            "id": "trust_signal",
            "type": "single_select",
            "title": "고객이 안심하고 예약하게 만드는 핵심 신뢰 요소는 무엇인가요?",
            "options": [
                option("reviews", "리뷰와 후기"),
                option("before_after", "전후 사진/결과물"),
                option("credentials", "자격/경력"),
                option("safety_process", "안전/위생 프로세스"),
            ],
        },
        {
            "id": "special_note",
            "type": "short_text",
            "title": "이 서비스에서 꼭 챙겨야 할 현장 변수는 무엇인가요?",
            "placeholder": "예: 반려견 성향, 픽업 여부, 예약 변경 빈도",
        },
    ] if pet_service or True else []


def build_ecommerce_questions(tags: list[str]) -> list[InterviewQuestion]:
    custom_product = "custom-products" in tags
    return [
        {
            "id": "product_focus",
            "type": "single_select_with_other",
            "title": "처음 밀고 싶은 대표 상품군은 무엇인가요?",
            "options": [
                option("hero_sku", "대표 SKU 1~2개"),
                option("small_collection", "작은 컬렉션"),
                option("personalized_order", "커스텀 주문형"),
                option("seasonal_drop", "시즌성 드롭 상품"),
                option("other", "기타 직접 입력"),
            ],
        },
        {
            "id": "margin_structure",
            "type": "single_select",
            "title": "마진 구조는 어느 쪽에 가까운가요?",
            "options": [
                option("high_margin_low_volume", "고마진 저빈도"),
                option("mid_margin_repeat", "중간 마진 + 반복 구매"),
                option("upsell_bundle", "번들/업셀 중심"),
                option("unknown", "아직 검증 전"),
            ],
        },
        {
            "id": "supply_model",
            "type": "single_select",
            "title": "공급 방식은 어떻게 운영할 계획인가요?",
            "options": [
                option("print_on_demand", "주문 후 제작/인쇄"),
                option("small_batch", "소량 선제작 재고"),
                option("dropshipping", "위탁/드랍쉬핑"),
                option("in_house", "직접 제작"),
            ],
        },
        {
            "id": "purchase_trigger",
            "type": "single_select_with_other",
            "title": "고객이 결제하는 가장 큰 이유는 무엇인가요?",
            "options": [
                option("identity", "개성/취향 표현"),
                option("gift", "선물 수요"),
                option("trend", "트렌드/팬심"),
                option("utility", "기능적 필요"),
                option("other", "기타 직접 입력"),
            ],
        },
        {
            "id": "competition_note",
            "type": "short_text",
            "title": "비슷한 상품이 많은데도 고객이 당신 것을 고를 이유는 무엇인가요?",
            "placeholder": custom_product and "예: 커스텀 시안 속도, 인쇄 퀄리티, 제작 리드타임" or "예: 디자인, 가격, 배송, 퀄리티",
        },
    ]


def build_content_questions(tags: list[str]) -> list[InterviewQuestion]:
    return [
        {
            "id": "content_format",
            "type": "single_select_with_other",
            "title": "핵심 콘텐츠 포맷은 무엇인가요?",
            "options": [
                option("short_form", "짧은 글/숏폼"),
                option("video", "영상"),
                option("newsletter", "뉴스레터"),
                option("community_post", "커뮤니티 글/토론"),
                option("other", "기타 직접 입력"),
            ],
        },
        {
            "id": "audience",
            "type": "single_select_with_other",
            "title": "처음 모을 핵심 이용자는 누구인가요?",
            "options": [
                option("students", "학생"),
                option("professionals", "직장인"),
                option("creators", "크리에이터"),
                option("niche_hobby", "특정 취미 커뮤니티"),
                option("other", "기타 직접 입력"),
            ],
        },
        {
            "id": "growth_channel",
            "type": "single_select",
            "title": "초기 유입은 어디서 만들 계획인가요?",
            "options": [
                option("instagram", "인스타그램/틱톡"),
                option("search", "검색/SEO"),
                option("community", "커뮤니티/입소문"),
                option("partnership", "제휴/콜라보"),
            ],
        },
        {
            "id": "monetization",
            "type": "single_select",
            "title": "수익화는 어떤 방식이 가장 자연스러운가요?",
            "options": [
                option("membership", "멤버십/구독"),
                option("ads", "광고/스폰서십"),
                option("course", "강의/디지털 상품"),
                option("commerce", "커머스 연계"),
            ],
        },
    ]


def build_general_questions() -> list[InterviewQuestion]:
    return [
        {
            "id": "target_user",
            "type": "single_select_with_other",
            "title": "가장 먼저 설득해야 할 고객은 누구인가요?",
            "options": [
                option("individuals", "개인 사용자"),
                option("small_business", "소상공인/중소팀"),
                option("creators", "크리에이터/프리랜서"),
                option("enterprise", "기업/조직"),
                option("other", "기타 직접 입력"),
            ],
        },
        {
            "id": "core_problem",
            "type": "short_text",
            "title": "그 고객이 지금 가장 답답해하는 문제를 한 줄로 적어주세요.",
            "placeholder": "예: 예약이 전화로만 들어와 운영이 꼬입니다",
        },
        {
            "id": "differentiation",
            "type": "short_text",
            "title": "기존 대안보다 무엇이 더 나아야 하나요?",
            "placeholder": "예: 더 빠른 실행, 더 낮은 비용, 더 높은 신뢰",
        },
        {
            "id": "revenue_model",
            "type": "single_select",
            "title": "수익은 주로 어디서 날 계획인가요?",
            "options": [
                option("subscription", "구독"),
                option("transaction", "거래 수수료"),
                option("service_fee", "서비스 요금"),
                option("product_sales", "상품 판매"),
            ],
        },
    ]


def generate_interview_plan(raw_idea: str) -> InterviewPlan:
    business_type = infer_business_type(raw_idea)
    tags = infer_tags(raw_idea)

    if business_type == "saas":
        questions = build_saas_questions(tags)
    elif business_type == "local_service":
        questions = build_local_service_questions(tags)
    elif business_type == "ecommerce":
        questions = build_ecommerce_questions(tags)
    elif business_type == "content_community":
        questions = build_content_questions(tags)
    else:
        questions = build_general_questions()

    return {
        "business_type": business_type,
        "tags": tags,
        "questions": questions[:5],
    }
