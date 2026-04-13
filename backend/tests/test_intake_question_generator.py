from agents.intake_question_generator import generate_interview_plan


def test_saas_questions_for_freelancer_time_tracking():
    plan = generate_interview_plan("Time tracking tool for freelancers")
    assert plan["business_type"] == "saas"
    assert "freelancer" in plan["tags"]
    assert any("프리랜서" in option["label"] for option in plan["questions"][0]["options"])


def test_local_service_questions_for_dog_grooming():
    plan = generate_interview_plan("Local dog grooming booking service")
    assert plan["business_type"] == "local_service"
    titles = [question["title"] for question in plan["questions"]]
    assert any("운영 지역" in title for title in titles)
    assert any("예약" in title for title in titles)


def test_ecommerce_questions_for_custom_phone_cases():
    plan = generate_interview_plan("Shopify store for custom phone cases")
    assert plan["business_type"] == "ecommerce"
    titles = [question["title"] for question in plan["questions"]]
    assert any("마진 구조" in title for title in titles)
    assert any("공급 방식" in title for title in titles)
