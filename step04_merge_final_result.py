# 04_merge_final_result.py
# 4단계: 프론트 전달용 최종 JSON 생성
# 입력:
# - output/evaluation_result.json
# - output/needs_improvement.json
# - output/feedback_detail.json
# - output/activity_recommendations.json
# 출력:
# - output/final_feedback_result.json

from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent

EVALUATION_FILE = BASE_DIR / "output" / "evaluation_result.json"
NEEDS_IMPROVEMENT_FILE = BASE_DIR / "output" / "needs_improvement.json"
FEEDBACK_FILE = BASE_DIR / "output" / "feedback_detail.json"
ACTIVITY_FILE = BASE_DIR / "output" / "activity_recommendations.json"

FINAL_OUTPUT_FILE = BASE_DIR / "output" / "final_feedback_result.json"


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def build_analysis_text(item):
    return (
        f"{item.get('reason', '')} "
        f"{item.get('improvement_direction', '')}"
    ).strip()


def build_summary(evaluation_data, needs_data):
    weak_keywords = needs_data.get("weak_keywords", [])

    if weak_keywords:
        weak_text = ", ".join(weak_keywords)
        summary_text = (
            f"지원자의 문서에서는 직무 관련 프로젝트 경험과 기술 활용 근거가 확인됩니다. "
            f"다만 {weak_text} 영역은 보완이 필요하므로, 공고 요구사항과 연결되는 경험·기술·성과를 더 구체화할 필요가 있습니다."
        )
    else:
        summary_text = (
            "지원자의 문서에서는 전반적인 직무 방향성과 프로젝트 경험이 확인됩니다. "
            "다만 각 경험의 문제 해결 과정, 기술 선택 이유, 성과를 더 구체적으로 정리하면 완성도를 높일 수 있습니다."
        )

    return {
        "title": "AI 종합 분석",
        "summary_text": summary_text,
        "weak_keywords": weak_keywords
    }


def build_main_weak_area(needs_data):
    return {
        "title": "보완 필요 영역",
        "weak_keywords": needs_data.get("weak_keywords", []),
        "items": list(needs_data.get("items", {}).values())
    }


def build_analysis_items(evaluation_data, feedback_data):
    items = []

    for key, evaluation in evaluation_data.items():
        feedback = feedback_data.get(key, {})

        item = {
            "key": key,
            "title": evaluation.get("criterion"),
            "meaning": evaluation.get("meaning"),
            "reference_basis": evaluation.get("reference_basis"),
            "level": evaluation.get("level"),
            "reason": evaluation.get("reason"),
            "strength_point": feedback.get("strength_point", ""),
            "weak_point": feedback.get("weak_point", ""),
            "improvement_direction": feedback.get("improvement_direction", "")
        }

        item["analysis_text"] = build_analysis_text(item)

        items.append(item)

    return items


def build_recommended_activities(activity_data):
    return {
        "title": "추천 활동",
        "status": activity_data.get("status", "success"),
        "based_on_weak_keywords": activity_data.get("based_on_weak_keywords", []),
        "items": activity_data.get("recommended_activities", [])
    }


def merge_result(evaluation_data, needs_data, feedback_data, activity_data):
    return {
        "ai_summary": build_summary(evaluation_data, needs_data),

        "main_weak_area": build_main_weak_area(needs_data),

        "analysis_description": {
            "title": "분석 내용 설명",
            "items": build_analysis_items(evaluation_data, feedback_data)
        },

        "recommended_activities": build_recommended_activities(activity_data)
    }


def main():
    evaluation_data = load_json(EVALUATION_FILE)
    needs_data = load_json(NEEDS_IMPROVEMENT_FILE)
    feedback_data = load_json(FEEDBACK_FILE)
    activity_data = load_json(ACTIVITY_FILE)

    final_result = merge_result(
        evaluation_data=evaluation_data,
        needs_data=needs_data,
        feedback_data=feedback_data,
        activity_data=activity_data
    )

    save_json(final_result, FINAL_OUTPUT_FILE)

    print("=== 4단계 최종 프론트 전달용 결과 생성 완료 ===")
    print(json.dumps(final_result, ensure_ascii=False, indent=2))
    print(f"\n저장 완료: {FINAL_OUTPUT_FILE}")


if __name__ == "__main__":
    main()