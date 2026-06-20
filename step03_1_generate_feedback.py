# step03_1_generate_feedback.py
# 3-1단계: 평가 결과와 근거 데이터를 바탕으로 사용자용 첨삭 문단 생성
# 입력:
# - output/evaluation_result.json
# - output/evidence.json
#
# 처리:
# - 2단계에서 생성된 level/reason을 읽는다.
# - 1단계 evidence 중 필요한 근거만 참고한다.
# - 항목별 analysis_text를 생성한다.
# - 항목별 평가 level을 종합해 AI 종합분석 overall_summary를 생성한다.
#
# 출력:
# - output/feedback_detail.json

from pathlib import Path
import json
import os
import anthropic


BASE_DIR = Path(__file__).resolve().parent

EVALUATION_FILE = BASE_DIR / "output" / "evaluation_result.json"
EVIDENCE_FILE = BASE_DIR / "output" / "evidence.json"
OUTPUT_FILE = BASE_DIR / "output" / "feedback_detail.json"

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


def call_sonnet(prompt, max_tokens=750):
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY 환경변수가 설정되어 있지 않습니다.")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    response = client.messages.create(
        model=MODEL_NAME,
        max_tokens=max_tokens,
        temperature=0,
        system=(
            "너는 IT 취업 지원서 첨삭 AI다. "
            "반드시 JSON만 출력한다. "
            "평가를 새로 수행하지 않고 제공된 평가 결과와 근거를 바탕으로 작성한다."
        ),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return extract_json(response.content[0].text)


def compact_feedback_evidence(key, evidence_data):
    evidence = evidence_data.get(key, {})

    if key == "job_fit":
        return {
            "job_required_skills": evidence.get("job_required_skills", []),
            "job_main_tasks": evidence.get("job_main_tasks", []),
            "job_requirements": evidence.get("job_requirements", []),
            "job_preferred": evidence.get("job_preferred", []),
            "matched_keywords": evidence.get("matched_keywords", []),
            "applicant_tech": evidence.get("applicant_tech", []),
            "applicant_core_keywords": evidence.get("applicant_core_keywords", []),
            "project_evidence": evidence.get("project_evidence", [])[:2]
        }

    if key == "experience_specificity":
        return {
            "project_evidence": evidence.get("project_evidence", [])[:3]
        }

    if key == "technical_competency":
        return {
            "used_technologies": evidence.get("used_technologies", []),
            "project_evidence": evidence.get("project_evidence", [])[:3]
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
            "extra_activities": evidence.get("extra_activities", [])
        }

    return evidence


def get_feedback_rule(key):
    if key == "job_fit":
        return """
- 공고 요구사항과 지원자 문서의 연결성을 설명한다.
- 공고와 직접 연결되는 기술 경험은 강점으로 설명한다.
- 공고에서 요구하지만 문서에서 덜 드러나는 요소는 보완 방향으로 설명한다.
- 새로운 기술 습득보다 현재 경험을 공고 요구사항과 더 잘 연결하는 표현 개선을 우선한다.
"""

    if key == "experience_specificity":
        return """
- STAR 관점에서 역할, 행동, 결과, 수치가 어떻게 드러나는지 설명한다.
- 수치 성과가 있으면 강점으로 설명하되, 측정 기준이나 기여도가 약하면 보완 방향으로 제시한다.
- 경험의 양보다 역할, 행동, 결과, 수치의 연결성이 어떻게 전달되는지 중심으로 설명한다.
"""

    if key == "technical_competency":
        return """
- 기술을 실제 구현, 데이터 처리, 문제 해결, 성과와 연결해 설명한다.
- 단순 기술 목록이 아니라 프로젝트 안에서 기술이 어떤 역할을 했는지 중심으로 설명한다.
- 보완 방향은 현재 프로젝트의 기술 선택 이유, 처리 규모, 개선 효과를 더 잘 드러내는 방식으로 제안한다.
"""

    if key == "document_quality":
        return """
- 문서 구조, 핵심 정보 포함 여부, 역할·성과·기술스택의 배치 관점으로 설명한다.
- ATS는 문서의 키워드와 구조화된 정보를 읽는 관점으로만 활용한다.
- 실제 PDF 디자인이나 시각적 편집 품질은 판단하지 않는다.
"""

    if key == "consistency_uniqueness":
        return """
- 프로젝트와 활동이 하나의 직무 방향성으로 연결되는지 설명한다.
- 반복적으로 드러나는 강점과 차별 포인트를 문서 근거에 기반해 설명한다.
- 새로운 직무 방향성을 억지로 제안하지 않는다.
"""

    return ""


def build_prompt(key, evaluation, evidence_data):
    feedback_evidence = compact_feedback_evidence(key, evidence_data)

    return f"""
아래 평가 결과와 근거를 바탕으로 사용자 화면에 보여줄 하나의 첨삭 문단을 작성해라.

[평가항목]
{evaluation.get("criterion")}

[평가 의미]
{evaluation.get("meaning")}

[참고 근거]
{evaluation.get("reference_basis")}

[평가 수준]
{evaluation.get("level")}

[평가 이유]
{evaluation.get("reason")}

[이력서/공고 근거]
{json.dumps(feedback_evidence, ensure_ascii=False)}

[항목별 작성 기준]
{get_feedback_rule(key)}

[피드백 작성 역할]
너는 취업 컨설턴트가 아니라 지원서 첨삭자다.
피드백의 목적은 지원자의 역량을 과하게 칭찬하거나 새 스펙을 추천하는 것이 아니라,
현재 문서에서 실제로 확인되는 내용과 충분히 전달되지 않는 내용을 구분해 설명하는 것이다.

[작성 흐름]
- 현재 문서에서 확인되는 강점을 설명한다.
- 해당 평가항목 기준에서 전달이 약한 부분을 설명한다.
- 현재 경험을 더 설득력 있게 보여주는 표현 개선 방향을 제안한다.

[평가 수준별 작성 원칙]
- level이 "우수"인 경우 강점 중심으로 작성하되, 완벽하거나 보완점이 전혀 없다고 표현하지 않는다.
- level이 "보통"인 경우 확인되는 강점과 주요 보완점을 균형 있게 작성한다.
- level이 "보완 필요"인 경우 부족하다고 단정하기보다 현재 문서에서 확인되지 않는 부분과 보완 방향을 구체적으로 작성한다.

[근거 사용 원칙]
- 평가를 다시 하지 않는다.
- 평가 이유와 제공된 근거에서 확인되는 내용만 사용한다.
- 2단계 평가 이유를 그대로 복사하지 않는다.
- 일반적인 취업 조언을 단독으로 제시하지 않는다.
- 새로운 경험, 자격증, 활동을 임의로 추가하지 않는다.
- 보완 방향은 새로운 스펙보다 현재 프로젝트·성과·기술 설명을 어떻게 더 잘 보여줄지 중심으로 작성한다.
- 문서에 없는 경험을 부족하다고 단정하지 않는다.
- 확인되지 않은 내용은 "현재 문서에서 확인되지 않는다" 또는 "현재 문서에서는 충분히 드러나지 않는다" 형태로 표현한다.
- 평가항목의 기준을 섞지 않는다.
- 확인되지 않은 사실을 단정하지 않는다.

[문체 기준]
- 사용자 화면에 바로 노출되는 하나의 자연스러운 첨삭 문단으로 작성한다.
- 칭찬문이 아니라 근거 기반 첨삭문으로 작성한다.
- 과도한 확신, 합격 단정, 완성도 단정을 피한다.
- 모든 문장은 "~입니다", "~합니다", "~할 수 있습니다" 문체로 통일한다.
- 3~4문장으로 작성한다.

[출력 형식]
{{
  "analysis_text": ""
}}
"""


def build_retry_prompt(key, evaluation, evidence_data, previous_result, error_reason):
    feedback_evidence = compact_feedback_evidence(key, evidence_data)

    return f"""
이전 피드백 결과에 문제가 있었다.

[오류 사유]
{error_reason}

[이전 결과]
{json.dumps(previous_result, ensure_ascii=False)}

아래 평가 결과와 근거를 바탕으로 JSON만 다시 출력해라.

[평가항목]
{evaluation.get("criterion")}

[평가 수준]
{evaluation.get("level")}

[평가 이유]
{evaluation.get("reason")}

[이력서/공고 근거]
{json.dumps(feedback_evidence, ensure_ascii=False)}

[출력 형식]
{{
  "analysis_text": ""
}}
"""


def validate_feedback(result):
    if not isinstance(result, dict):
        return False, "결과가 JSON 객체가 아닙니다."

    if "analysis_text" not in result:
        return False, "analysis_text 필드가 없습니다."

    if not isinstance(result["analysis_text"], str):
        return False, "analysis_text 값이 문자열이 아닙니다."

    if not result["analysis_text"].strip():
        return False, "analysis_text 값이 비어 있습니다."

    forbidden = [
        "합격 보장",
        "무조건 합격",
        "반드시 합격"
    ]

    if any(word in result["analysis_text"] for word in forbidden):
        return False, "부적절한 표현이 포함되어 있습니다."

    return True, ""


def failed_feedback(error_reason):
    return {
        "status": "failed",
        "analysis_text": "",
        "error_reason": error_reason
    }


def generate_feedback_for_criterion(key, evaluation, evidence_data):
    prompt = build_prompt(key, evaluation, evidence_data)
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
                        evaluation=evaluation,
                        evidence_data=evidence_data,
                        previous_result=previous_result,
                        error_reason=error_reason
                    )
                )

            is_valid, error_reason = validate_feedback(result)

            if is_valid:
                result["status"] = "success"
                return result

            print(f"{attempt}차 피드백 검증 실패 ({evaluation.get('criterion')}): {error_reason}")
            previous_result = result

        except Exception as e:
            error_reason = str(e)
            print(f"{attempt}차 피드백 생성 실패 ({evaluation.get('criterion')}): {error_reason}")
            previous_result = {}

    return failed_feedback(error_reason)


def build_summary_prompt(feedback_items):
    summary_input = {
        key: {
            "criterion": item.get("criterion"),
            "level": item.get("level"),
            "reason": item.get("reason")
        }
        for key, item in feedback_items.items()
    }

    return f"""
아래 5개 평가항목 결과를 바탕으로 사용자 화면 상단의 AI 종합 분석 문장을 작성해라.

[평가 결과]
{json.dumps(summary_input, ensure_ascii=False)}

[작성 목적]
- 사용자가 전체 이력서 평가 결과를 한눈에 이해하도록 돕는다.
- 세부 기술명을 많이 나열하지 말고, 5개 평가영역 중 강점 영역과 보완 영역을 중심으로 요약한다.
- 각 평가영역의 level을 우선 반영한다.
- "우수"로 평가된 영역은 강점 영역으로 묶어 설명한다.
- "보통" 또는 "보완 필요"로 평가된 영역은 우선 보완 영역으로 설명한다.
- 항목별 세부 피드백을 반복하지 않는다.
- 새로운 경험이나 활동을 추천하지 않는다.
- 합격 가능성을 단정하지 않는다.

[작성 흐름]
1. 전체 평가 흐름을 한 문장으로 요약한다.
2. 강점으로 평가된 영역을 1문장으로 묶어 설명한다.
3. 보완이 필요한 영역을 1문장으로 설명한다.

[문체 기준]
- 사용자 화면의 "AI 종합 분석" 카드에 들어갈 문장이다.
- 친절하지만 과장 없는 첨삭 톤으로 작성한다.
- 전반적인 수준을 표현할 때도 "완성도 높은 이력서"처럼 단정하지 말고 "완성도가 높은 편입니다", "강점으로 확인됩니다"처럼 근거 기반 표현을 사용한다.
- 모든 문장은 "~입니다", "~합니다", "~할 수 있습니다" 문체로 통일한다.
- 2~3문장으로 작성한다.

[출력 형식]
{{
  "title": "AI 종합 분석",
  "summary_text": ""
}}
"""


def validate_summary(result):
    if not isinstance(result, dict):
        return False, "결과가 JSON 객체가 아닙니다."

    if result.get("title") != "AI 종합 분석":
        return False, "title 값이 올바르지 않습니다."

    if not isinstance(result.get("summary_text"), str) or not result.get("summary_text").strip():
        return False, "summary_text 값이 비어 있습니다."

    forbidden = [
        "합격 보장",
        "무조건 합격",
        "반드시 합격"
    ]

    if any(word in result["summary_text"] for word in forbidden):
        return False, "부적절한 표현이 포함되어 있습니다."

    return True, ""


def generate_overall_summary(feedback_items):
    prompt = build_summary_prompt(feedback_items)
    previous_result = {}
    error_reason = ""

    for attempt in range(1, 3):
        try:
            if attempt == 1:
                result = call_sonnet(prompt, max_tokens=450)
            else:
                retry_prompt = f"""
이전 AI 종합 분석 결과에 문제가 있었다.

[오류 사유]
{error_reason}

[이전 결과]
{json.dumps(previous_result, ensure_ascii=False)}

아래 형식으로 JSON만 다시 출력해라.

[출력 형식]
{{
  "title": "AI 종합 분석",
  "summary_text": ""
}}
"""
                result = call_sonnet(retry_prompt, max_tokens=300)

            is_valid, error_reason = validate_summary(result)

            if is_valid:
                result["status"] = "success"
                return result

            print(f"{attempt}차 종합분석 검증 실패: {error_reason}")
            previous_result = result

        except Exception as e:
            error_reason = str(e)
            print(f"{attempt}차 종합분석 생성 실패: {error_reason}")
            previous_result = {}

    return {
        "title": "AI 종합 분석",
        "summary_text": "",
        "status": "failed",
        "error_reason": error_reason
    }


def main():
    evaluation_data = load_json(EVALUATION_FILE)
    evidence_data = load_json(EVIDENCE_FILE)

    feedback_items = {}

    print("=== 3-1단계 Sonnet 근거 기반 첨삭 문단 생성 시작 ===")

    for key, evaluation in evaluation_data.items():
        print(f"{evaluation.get('criterion')} 첨삭 문단 생성 중...")

        feedback = generate_feedback_for_criterion(
            key=key,
            evaluation=evaluation,
            evidence_data=evidence_data
        )

        feedback_items[key] = {
            "criterion": evaluation.get("criterion"),
            "meaning": evaluation.get("meaning"),
            "reference_basis": evaluation.get("reference_basis"),
            "status": feedback.get("status", "success"),
            "level": evaluation.get("level", ""),
            "reason": evaluation.get("reason", ""),
            "analysis_text": feedback.get("analysis_text", "")
        }

        if feedback.get("status") == "failed":
            feedback_items[key]["error_reason"] = feedback.get("error_reason", "")

        print(json.dumps(feedback_items[key], ensure_ascii=False, indent=2))

    print("\n=== AI 종합 분석 생성 중 ===")

    overall_summary = generate_overall_summary(feedback_items)

    final_result = {
        "overall_summary": overall_summary,
        "items": feedback_items
    }

    save_json(final_result, OUTPUT_FILE)

    print("\n=== 3-1단계 Sonnet 근거 기반 첨삭 문단 생성 완료 ===")
    print(json.dumps(final_result, ensure_ascii=False, indent=2))
    print(f"\n저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()