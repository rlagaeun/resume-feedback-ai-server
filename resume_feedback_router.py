# resume_feedback_router.py

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(
    prefix="/resume/analyze",
    tags=["Resume Feedback AI"]
)


# =========================
# Response Models
# =========================

class FeedbackItem(BaseModel):
    category: str
    content: str


class WeakArea(BaseModel):
    category: str
    reason: str


class FeedbackResponse(BaseModel):
    feedbacks: List[FeedbackItem]
    weak_areas: List[WeakArea]


class ActivityItem(BaseModel):
    title: str
    description: str


class ActivitiesResponse(BaseModel):
    recommended_activities: List[ActivityItem]


# =========================
# Feedback API
# =========================

@router.post(
    "/feedback",
    response_model=FeedbackResponse
)
def analyze_resume_feedback(request: Dict[str, Any]):
    """
    이력서 AI 피드백 분석 엔드포인트

    POST /resume/analyze/feedback

    Request Body는 Spring ↔ FastAPI 연동 방식 확정 후 구체화 예정입니다.
    현재는 엔드포인트 구조와 Response 형식 확인을 위한 임시 코드입니다.
    """

    try:
        # TODO:
        # 1. request에서 통합 이력서 데이터 추출
        # 2. request에서 선택 채용공고 데이터 추출
        # 3. step01_extract_evidence 실행
        # 4. step02_evaluate_level 실행
        # 5. step03_1_generate_feedback 실행
        # 6. 필요한 값만 아래 형식으로 반환

        return {
            "feedbacks": [
                {
                    "category": "직무 적합도",
                    "content": ""
                },
                {
                    "category": "경험·성과 구체성",
                    "content": ""
                },
                {
                    "category": "실무·기술 역량",
                    "content": ""
                },
                {
                    "category": "문서 완성도",
                    "content": ""
                },
                {
                    "category": "경험 일관성·차별성",
                    "content": ""
                }
            ],
            "weak_areas": [
                {
                    "category": "",
                    "reason": ""
                }
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =========================
# Activities API
# =========================

@router.post(
    "/activities",
    response_model=ActivitiesResponse
)
def analyze_resume_activities(request: Dict[str, Any]):
    """
    추천활동 생성 엔드포인트

    POST /resume/analyze/activities

    Request Body는 Spring ↔ FastAPI 연동 방식 확정 후 구체화 예정입니다.
    현재는 엔드포인트 구조와 Response 형식 확인을 위한 임시 코드입니다.
    """

    try:
        # TODO:
        # 1. request에서 evidence_data 추출
        # 2. request에서 evaluation_result 데이터 추출
        # 3. request에서 needs_improvement 데이터 추출
        # 4. step03_2_generate_activities 실행
        # 5. 필요한 값만 아래 형식으로 반환

        return {
            "recommended_activities": [
                {
                    "title": "",
                    "description": ""
                },
                {
                    "title": "",
                    "description": ""
                },
                {
                    "title": "",
                    "description": ""
                }
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))