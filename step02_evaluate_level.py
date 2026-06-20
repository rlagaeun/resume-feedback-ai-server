# step02_evaluate_level.py
# 2단계: evidence.json을 기반으로 Sonnet이 평가 수준을 판단
# 입력:
# - output/evidence.json
#
# 처리:
# - 1단계에서 정리된 공고/이력서 근거를 읽는다.
# - 코드가 부족 항목을 판단하지 않고, Sonnet이 직접 비교한다.
# - 5개 평가항목별로 level/reason을 생성한다.
# - level이 "보완 필요"인 항목만 needs_improvement.json에 따로 저장한다.
#
# 출력:
# - output/evaluation_result.json
# - output/needs_improvement.json

from pathlib import Path
import json
import os
import anthropic


BASE_DIR = Path(__file__).resolve().parent

EVIDENCE_FILE = BASE_DIR / "output" / "evidence.json"
OUTPUT_FILE = BASE_DIR / "output" / "evaluation_result.json"
NEEDS_IMPROVEMENT_FILE = BASE_DIR / "output" / "needs_improvement.json"

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# 필요하면 PowerShell에서 직접 바꿀 수 있음:
# $env:CLAUDE_MODEL_NAME="claude-sonnet-4-6"
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


def call_sonnet(prompt, max_tokens=500):
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않습니다.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=max_tokens,
        temperature=0,
        system=(
            "너는 IT 취업 지원서 평가 AI다. "
            "반드시 JSON만 출력한다. "
            "근거에 없는 내용은 지어내지 않는다."
        ),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return extract_json(response.content[0].text)


def compact_evidence(key, evidence):
    if key == "job_fit":
        return {
            "job_title": evidence.get("job_title"),
            "company_name": evidence.get("company_name"),
            "job_required_skills": evidence.get("job_required_skills", []),
            "job_main_tasks": evidence.get("job_main_tasks", []),
            "job_requirements": evidence.get("job_requirements", []),
            "job_preferred": evidence.get("job_preferred", []),
            "job_talent": evidence.get("job_talent", []),
            "matched_keywords": evidence.get("matched_keywords", []),
            "applicant_tech": evidence.get("applicant_tech", []),
            "applicant_core_keywords": evidence.get("applicant_core_keywords", []),
            "project_evidence": evidence.get("project_evidence", [])[:5]
        }

    if key == "experience_specificity":
        return {
            "project_evidence": evidence.get("project_evidence", [])[:5]
        }

    if key == "technical_competency":
        return {
            "used_technologies": evidence.get("used_technologies", []),
            "project_evidence": evidence.get("project_evidence", [])[:5]
        }

    if key == "document_quality":
        return {
            "document_quality_signals": evidence.get("document_quality_signals", {})
        }

    if key == "consistency_uniqueness":
        return {
            "core_keywords": evidence.get("core_keywords", []),
            "keyword_frequency": evidence.get("keyword_frequency", {}),
            "repeated_strength_keywords": evidence.get("repeated_strength_keywords", []),
            "project_names": evidence.get("project_names", []),
            "awards_certificates": evidence.get("awards_certificates", []),
            "extra_activities": evidence.get("extra_activities", []),
            "project_evidence": evidence.get("project_evidence", [])[:5]
        }

    return evidence


def get_evaluation_rule(key):
    if key == "job_fit":
        return """
채용공고의 요구기술, 주요업무, 자격요건과 지원자의 기술스택·프로젝트 경험이 얼마나 직접 연결되는지 평가한다.
matched_keywords는 참고자료일 뿐이며, 최종 판단은 공고 요구사항과 프로젝트 원문을 직접 비교해 수행한다.
"""

    if key == "experience_specificity":
        return """
STAR 방식 관점에서 역할, 행동, 결과, 수치가 얼마나 구체적으로 드러나는지 평가한다.
프로젝트가 많다는 이유만으로 우수로 판단하지 않는다.
"""

    if key == "technical_competency":
        return """
기술을 실제 구현, 데이터 처리, 문제 해결, 성과 창출에 활용한 근거를 평가한다.
단순 기술 목록이 아니라 프로젝트에서의 사용 맥락을 본다.
"""

    if key == "document_quality":
        return """
ATS/이력서 첨삭 관점에서 문서 구조, 핵심 정보 포함 여부, 평가자가 읽기 쉬운 근거 구성을 평가한다.
단, 원본 디자인이 아니라 추출된 분석 JSON 구조 기준으로만 판단한다.
"""

    if key == "consistency_uniqueness":
        return """
프로젝트와 활동이 하나의 직무 방향성으로 연결되는지, 반복적으로 드러나는 강점과 차별 포인트가 있는지 평가한다.
단순 반복 키워드가 아니라 경험 간 연결성을 본다.
"""

    return ""


def build_prompt(key, evidence):
    return f"""
아래 평가항목에 대해 지원자 문서를 평가해라.

[평가항목]
{evidence.get("criterion")}

[평가 의미]
{evidence.get("meaning")}

[참고 근거]
{evidence.get("reference_basis")}

[평가 기준]
{get_evaluation_rule(key)}

[평가 근거]
{json.dumps(compact_evidence(key, evidence), ensure_ascii=False)}

[판단 기준]
- level은 반드시 "우수", "보통", "보완 필요" 중 하나만 선택한다.
- 우수: 해당 항목의 근거가 충분하고, 채용공고 또는 평가기준과 직접 연결된다.
- 보통: 관련 근거는 있으나 직접성, 구체성, 깊이가 일부 부족하다.
- 보완 필요: 핵심 근거가 부족하거나 채용공고/평가기준과의 연결성이 약하다.
- 공고 요구사항과 지원자 근거를 직접 비교해 판단한다.
- 코드가 부족 키워드를 미리 판단하지 않았으므로, 부족 여부는 평가 근거 전체를 보고 직접 판단한다.
- 근거가 애매하면 과대평가하지 않는다.
- 근거에 없는 내용을 지어내지 않는다.
- reason은 1~2문장으로 작성한다.
- 합격 가능성을 단정하지 않는다.

[출력 형식]
{{
  "level": "",
  "reason": ""
}}
"""


def build_retry_prompt(key, evidence, previous_result, error_reason):
    return f"""
이전 평가 결과에 문제가 있었다.

[오류 사유]
{error_reason}

[이전 결과]
{json.dumps(previous_result, ensure_ascii=False)}

아래 형식에 맞춰 JSON만 다시 출력해라.

[평가항목]
{evidence.get("criterion")}

[평가 근거]
{json.dumps(compact_evidence(key, evidence), ensure_ascii=False)}

[출력 형식]
{{
  "level": "",
  "reason": ""
}}
"""


def validate_result(result):
    if not isinstance(result, dict):
        return False, "결과가 JSON 객체가 아닙니다."

    if result.get("level") not in ["우수", "보통", "보완 필요"]:
        return False, "level 값이 올바르지 않습니다."

    if not isinstance(result.get("reason"), str) or not result.get("reason").strip():
        return False, "reason 값이 비어 있습니다."

    forbidden = [
        "하겠습니다",
        "합격 보장",
        "무조건 합격",
        "반드시 합격",
        "합격 가능성이 높습니다",
        "합격 가능성이 낮습니다"
    ]

    if any(word in result.get("reason", "") for word in forbidden):
        return False, "부적절한 단정 표현이 포함되어 있습니다."

    return True, ""


def failed_result(error_reason):
    return {
        "status": "failed",
        "level": "",
        "reason": f"AI 평가 생성 실패: {error_reason}"
    }


def evaluate_criterion(key, evidence):
    prompt = build_prompt(key, evidence)
    previous_result = {}
    error_reason = ""

    for attempt in range(1, 3):
        try:
            if attempt == 1:
                result = call_sonnet(prompt)
            else:
                result = call_sonnet(
                    build_retry_prompt(
                        key=key,
                        evidence=evidence,
                        previous_result=previous_result,
                        error_reason=error_reason
                    )
                )

            is_valid, error_reason = validate_result(result)

            if is_valid:
                result["status"] = "success"
                return result

            print(f"{attempt}차 평가 검증 실패 ({evidence.get('criterion')}): {error_reason}")
            previous_result = result

        except Exception as e:
            error_reason = str(e)
            print(f"{attempt}차 평가 생성 실패 ({evidence.get('criterion')}): {error_reason}")
            previous_result = {}

    return failed_result(error_reason)


def build_missing_detail(key, evidence):
    if key == "job_fit":
        return {
            "job_required_skills": evidence.get("job_required_skills", []),
            "job_main_tasks": evidence.get("job_main_tasks", []),
            "job_requirements": evidence.get("job_requirements", []),
            "job_preferred": evidence.get("job_preferred", []),
            "matched_keywords": evidence.get("matched_keywords", []),
            "applicant_tech": evidence.get("applicant_tech", []),
            "applicant_core_keywords": evidence.get("applicant_core_keywords", [])
        }

    if key == "experience_specificity":
        return {
            "project_evidence": evidence.get("project_evidence", [])[:5]
        }

    if key == "technical_competency":
        return {
            "used_technologies": evidence.get("used_technologies", []),
            "project_evidence": evidence.get("project_evidence", [])[:5]
        }

    if key == "document_quality":
        return {
            "document_quality_signals": evidence.get("document_quality_signals", {})
        }

    if key == "consistency_uniqueness":
        return {
            "core_keywords": evidence.get("core_keywords", []),
            "keyword_frequency": evidence.get("keyword_frequency", {}),
            "project_names": evidence.get("project_names", []),
            "awards_certificates": evidence.get("awards_certificates", []),
            "extra_activities": evidence.get("extra_activities", [])
        }

    return {}


def build_needs_improvement(evaluation_data, evidence_data):
    items = {}

    for key, evaluation in evaluation_data.items():
        if evaluation.get("level") == "보완 필요":
            evidence = evidence_data.get(key, {})

            items[key] = {
                "key": key,
                "criterion": evaluation.get("criterion"),
                "meaning": evaluation.get("meaning"),
                "reference_basis": evaluation.get("reference_basis"),
                "level": evaluation.get("level"),
                "reason": evaluation.get("reason"),
                "main_screen_keyword": evaluation.get("criterion"),
                "detail": build_missing_detail(key, evidence)
            }

    return {
        "weak_keywords": [
            item["main_screen_keyword"]
            for item in items.values()
        ],
        "items": items
    }


def main():
    evidence_data = load_json(EVIDENCE_FILE)

    evaluation_data = {}

    print("=== 2단계 Sonnet 평가 시작 ===")

    for key, evidence in evidence_data.items():
        if key == "selected_job":
            continue

        print(f"{evidence.get('criterion')} 평가 중...")

        result = evaluate_criterion(key, evidence)

        evaluation_data[key] = {
            "criterion": evidence.get("criterion"),
            "meaning": evidence.get("meaning"),
            "reference_basis": evidence.get("reference_basis"),
            "status": result.get("status", "success"),
            "level": result.get("level", ""),
            "reason": result.get("reason", "")
        }

        print(json.dumps(evaluation_data[key], ensure_ascii=False, indent=2))

    needs_improvement = build_needs_improvement(evaluation_data, evidence_data)

    save_json(evaluation_data, OUTPUT_FILE)
    save_json(needs_improvement, NEEDS_IMPROVEMENT_FILE)

    print("\n=== 2단계 Sonnet 평가 완료 ===")
    print(f"전체 평가 저장 완료: {OUTPUT_FILE}")
    print(f"보완 필요 저장 완료: {NEEDS_IMPROVEMENT_FILE}")


if __name__ == "__main__":
    main()