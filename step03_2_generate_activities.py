# step03_2_generate_activities.py
# 3-2단계: 취업 가능성을 높이는 추천활동 카드 3개 생성
#
# 입력:
# - output/evidence.json
# - output/evaluation_result.json
# - output/needs_improvement.json
#
# 처리:
# - 현재 선택된 공고와 이력서 분석 결과를 기준으로 추천활동 3개를 생성한다.
# - 개인 성장보다 해당 공고/직무 지원에 도움이 되는 활동을 우선 추천한다.
# - UI 카드에 맞게 title, description, category만 생성한다.
# - 추천활동 3개 전체 JSON과 개별 JSON을 모두 저장한다.
#
# 출력:
# - output/activity_recommendations.json
# - output/activity_recommendations/activity_1.json
# - output/activity_recommendations/activity_2.json
# - output/activity_recommendations/activity_3.json

from pathlib import Path
import json
import os
import anthropic


BASE_DIR = Path(__file__).resolve().parent

EVIDENCE_FILE = BASE_DIR / "output" / "evidence.json"
EVALUATION_FILE = BASE_DIR / "output" / "evaluation_result.json"
NEEDS_IMPROVEMENT_FILE = BASE_DIR / "output" / "needs_improvement.json"

OUTPUT_FILE = BASE_DIR / "output" / "activity_recommendations.json"
INDIVIDUAL_OUTPUT_DIR = BASE_DIR / "output" / "activity_recommendations"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MODEL_NAME = os.getenv("CLAUDE_MODEL_NAME", "claude-sonnet-4-6")


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def extract_json(text):
    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        raise ValueError("JSON not found")

    return json.loads(text[start:end + 1])


def call_sonnet(prompt):
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않습니다.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=800,
        temperature=0,
        system=(
            "너는 IT 취업 준비 추천활동 생성 AI다. "
            "반드시 유효한 JSON만 출력한다. "
            "마크다운, 코드블록, 설명 문장은 출력하지 않는다."
        ),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return extract_json(response.content[0].text)


def compact_context(evidence_data, evaluation_data, needs_data):
    selected_job = evidence_data.get("selected_job", {})
    job_fit = evidence_data.get("job_fit", {})

    return {
        "target_job": {
            "site": selected_job.get("site"),
            "category": selected_job.get("category"),
            "company_name": selected_job.get("company_name"),
            "job_title": selected_job.get("job_title")
        },

        "job_requirements": {
            "required_skills": job_fit.get("job_required_skills", []),
            "preferred": job_fit.get("job_preferred", []),
            "main_tasks": job_fit.get("job_main_tasks", [])[:5]
        },

        "applicant": {
            "skills": job_fit.get("applicant_tech", [])[:30],
            "matched_keywords": job_fit.get("matched_keywords", [])[:20],
            "core_keywords": job_fit.get("applicant_core_keywords", [])[:15]
        },

        "evaluation": {
            key: {
                "criterion": value.get("criterion"),
                "level": value.get("level")
            }
            for key, value in evaluation_data.items()
        },

        "needs_improvement": {
            "weak_keywords": needs_data.get("weak_keywords", []),
            "items": needs_data.get("items", {})
        }
    }


def build_prompt(context):
    return f"""
아래 정보를 보고 추천활동 카드 3개를 생성해라.

[분석 정보]
{json.dumps(context, ensure_ascii=False)}

[추천 목적]
- 추천활동은 단순한 개인 성장용 조언이 아니다.
- 사용자가 지원하려는 공고와 직무에서 더 좋게 평가받기 위한 활동을 추천한다.
- 이력서에서 부족하거나 덜 드러나는 역량이 있으면 그것을 우선 보완한다.
- 부족한 부분이 많으면 추천 3개 모두 보완 활동이어도 된다.

[추천 우선순위]
1. 공고에서 요구하지만 현재 이력서에서 확인되지 않는 역량
2. 공고에서 중요하지만 현재 이력서에서 약하게 드러나는 역량
3. 공고 필수/우대사항과 연결되는 공식 자격증, 공식 교육, 공식 실습, 프로젝트
4. 이미 가진 강점을 취업용 포트폴리오로 더 잘 보여줄 수 있는 활동

[추천활동 구성 기준]
- 추천활동은 정확히 3개만 작성한다.
- 가능하면 3개 중 최소 1개는 자격증, 공식 교육, 공식 실습처럼 사용자가 바로 이해할 수 있는 명확한 활동으로 제안한다.
- 단, 지원 직무와 연결성이 낮은 자격증을 억지로 추천하지 않는다.
- 자격증을 추천할 때는 실제 존재하는 공식 자격증명만 사용한다.
- 정확한 자격증명이 확실하지 않으면 자격증 대신 공식 교육, 공식 실습, 또는 포트폴리오 프로젝트를 추천한다.
- 자격증명은 임의로 번역하거나 축약하지 않는다.
- 포트폴리오 개선만 3개 추천하지 않는다.
- 단순한 공부 권유보다 결과물이 남는 활동을 우선한다.

[카드 작성 기준]
- title은 화면 카드 제목처럼 짧고 명확하게 작성한다.
- description은 화면 카드에 들어갈 1문장으로 작성한다.
- description은 해당 활동이 취업 준비에 어떻게 도움이 되는지를 중심으로 작성한다.
- "부족", "감점", "낮은 평가"처럼 부정적으로 들리는 표현은 피한다.
- "열심히 공부하기", "기본기 쌓기"처럼 추상적인 표현은 사용하지 않는다.
- "서류 단계", "채용 담당자에게", "평가받을 수 있다", "합격 가능성"처럼 채용 결과를 직접 예측하거나 암시하는 표현은 사용하지 않는다.
- 역량을 어떻게 보여줄 수 있는지, 어떤 결과물을 만들 수 있는지 중심으로 설명한다.
- 합격 가능성을 단정하지 않는다.

[category 허용값]
자격증, 프로젝트, 실습, 포트폴리오 개선, 학습

[출력 형식]
반드시 아래 JSON 형식만 출력해라.

{{
  "recommended_activities": [
    {{
      "title": "",
      "description": "",
      "category": ""
    }},
    {{
      "title": "",
      "description": "",
      "category": ""
    }},
    {{
      "title": "",
      "description": "",
      "category": ""
    }}
  ]
}}
"""


def validate_activities(result):
    if not isinstance(result, dict):
        return False, "결과가 JSON 객체가 아닙니다."

    activities = result.get("recommended_activities")

    if not isinstance(activities, list):
        return False, "recommended_activities가 리스트가 아닙니다."

    if len(activities) != 3:
        return False, "추천활동은 반드시 3개여야 합니다."

    allowed_categories = [
        "자격증",
        "프로젝트",
        "실습",
        "포트폴리오 개선",
        "학습"
    ]

    for index, activity in enumerate(activities, start=1):
        if not isinstance(activity, dict):
            return False, f"{index}번째 추천활동이 객체가 아닙니다."

        for field in ["title", "description", "category"]:
            if field not in activity:
                return False, f"{index}번째 추천활동에 {field} 필드가 없습니다."

            if not isinstance(activity[field], str):
                return False, f"{index}번째 추천활동의 {field} 값이 문자열이 아닙니다."

            if not activity[field].strip():
                return False, f"{index}번째 추천활동의 {field} 값이 비어 있습니다."

        if activity["category"] not in allowed_categories:
            return False, f"{index}번째 추천활동 category가 허용값이 아닙니다."

    joined = " ".join(
        activity["title"] + " " + activity["description"]
        for activity in activities
    )

    forbidden = [
        "합격 보장",
        "무조건 합격",
        "반드시 합격",
        "열심히 공부",
        "기본기 쌓기",
        "아무 활동",
        "관련 없음",
        "감점",
        "낮은 평가"
    ]

    if any(word in joined for word in forbidden):
        return False, "부적절하거나 추상적인 표현이 포함되어 있습니다."

    return True, ""


def failed_result(error_reason):
    return {
        "status": "failed",
        "message": "AI 추천활동 생성에 실패했습니다.",
        "error_reason": error_reason,
        "recommended_activities": []
    }


def generate_activities(evidence_data, evaluation_data, needs_data):
    context = compact_context(
        evidence_data=evidence_data,
        evaluation_data=evaluation_data,
        needs_data=needs_data
    )

    prompt = build_prompt(context)

    try:
        result = call_sonnet(prompt)

        is_valid, error_reason = validate_activities(result)

        if not is_valid:
            print(f"추천활동 검증 실패: {error_reason}")
            return failed_result(error_reason)

        result["status"] = "success"
        return result

    except Exception as e:
        error_reason = str(e)
        print(f"추천활동 생성 실패: {error_reason}")
        return failed_result(error_reason)


def save_individual_activities(result):
    activities = result.get("recommended_activities", [])

    for index, activity in enumerate(activities, start=1):
        individual_result = {
            "status": result.get("status", "success"),
            "activity_index": index,
            "activity": activity
        }

        save_json(
            individual_result,
            INDIVIDUAL_OUTPUT_DIR / f"activity_{index}.json"
        )


def main():
    evidence_data = load_json(EVIDENCE_FILE)
    evaluation_data = load_json(EVALUATION_FILE)
    needs_data = load_json(NEEDS_IMPROVEMENT_FILE)

    print("=== 3-2단계 Sonnet 추천활동 생성 시작 ===")

    result = generate_activities(
        evidence_data=evidence_data,
        evaluation_data=evaluation_data,
        needs_data=needs_data
    )

    save_json(result, OUTPUT_FILE)
    save_individual_activities(result)

    print("\n=== 3-2단계 Sonnet 추천활동 생성 완료 ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"\n전체 추천활동 저장 완료: {OUTPUT_FILE}")
    print(f"개별 추천활동 저장 완료: {INDIVIDUAL_OUTPUT_DIR}")


if __name__ == "__main__":
    main()