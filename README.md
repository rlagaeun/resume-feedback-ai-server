# 이력서 분석 API 명세서

## 1. 개요

사용자의 이력서, 자기소개서, 포트폴리오와 선택한 채용공고 정보를 기반으로 AI 분석을 수행한다.

분석 결과는 다음과 같이 제공된다.

- AI 종합 분석
- 5개 평가영역별 피드백
- 보완 필요 키워드
- 추천활동 3개

---

## 2. AI 피드백 분석

### POST /resume/analyze/feedback

이력서·자기소개서·포트폴리오와 선택 채용공고 정보를 기반으로 AI 피드백 분석을 수행한다.

> Request Body는 Spring ↔ FastAPI 연동 방식 확정 후 작성 예정

### 사용 데이터

| 데이터 | 설명 |
|----------|----------|
| 통합 이력서 데이터 | 이력서·자기소개서·포트폴리오를 통합한 지원자 정보 |
| 선택 채용공고 데이터 | 분석 기준이 되는 회사 공고 정보 |
| evidence.json | 이력서와 공고 비교 근거 |
| evaluation_result.json | 5개 평가영역 평가 결과 |
| feedback_detail.json | AI 종합 분석 및 5개 영역별 피드백 |
| needs_improvement.json | 보완 필요 키워드 및 항목 |

### Response

```json
{
  "overall_summary": {
    "title": "AI 종합 분석",
    "summary_text": "경험·성과 구체성, 실무·기술 역량, 문서 완성도, 경험 일관성·차별성 영역에서 강점이 확인됩니다. 다만 직무 적합도 측면에서 공고가 요구하는 일부 기술 경험이 문서에 충분히 드러나지 않아 보완이 필요합니다."
  },

  "items": {
    "job_fit": {
      "criterion": "직무 적합도",
      "meaning": "JD/NCS 기반 직무 연관성",
      "reference_basis": "NCS 직무기술서 + 고용24 채용공고",
      "status": "success",
      "level": "보통",
      "reason": "...",
      "analysis_text": "..."
    },

    "experience_specificity": {
      "criterion": "경험·성과 구체성",
      "meaning": "역할·행동·결과·수치",
      "reference_basis": "STAR 경험 평가 방식",
      "status": "success",
      "level": "우수",
      "reason": "...",
      "analysis_text": "..."
    },

    "technical_competency": {
      "criterion": "실무·기술 역량",
      "meaning": "기술 활용·구현·문제 해결",
      "reference_basis": "NCS 직무 수행 역량 + 개발자 포트폴리오 평가 관점",
      "status": "success",
      "level": "우수",
      "reason": "...",
      "analysis_text": "..."
    },

    "document_quality": {
      "criterion": "문서 완성도",
      "meaning": "가독성·구조·핵심 전달",
      "reference_basis": "ATS/이력서 첨삭 관점",
      "status": "success",
      "level": "우수",
      "reason": "...",
      "analysis_text": "..."
    },

    "consistency_uniqueness": {
      "criterion": "경험 일관성·차별성",
      "meaning": "경험 연결성·본인만의 강점",
      "reference_basis": "자기소개서 첨삭 및 직무 방향성 평가 관점",
      "status": "success",
      "level": "우수",
      "reason": "...",
      "analysis_text": "..."
    }
  },

  "needs_improvement": {
    "weak_keywords": [],
    "items": {}
  }
}
```

### 응답 필드

#### overall_summary

| 필드 | 타입 | 설명 |
|----------|----------|----------|
| title | string | 종합 분석 제목 |
| summary_text | string | 5개 평가영역을 종합한 분석 문장 |

---

#### items

5개 평가영역별 분석 결과

| key | 화면 표시명 |
|----------|----------|
| job_fit | 직무 적합도 |
| experience_specificity | 경험·성과 구체성 |
| technical_competency | 실무·기술 역량 |
| document_quality | 문서 완성도 |
| consistency_uniqueness | 경험 일관성·차별성 |

---

#### 평가영역 객체

| 필드 | 타입 | 설명 |
|----------|----------|----------|
| criterion | string | 평가 항목명 |
| meaning | string | 평가 항목 의미 |
| reference_basis | string | 평가 기준 근거 |
| status | string | 생성 성공 여부 |
| level | string | 평가 수준 |
| reason | string | 평가 이유 |
| analysis_text | string | 사용자 화면 표시용 피드백 |

---

#### level 값

| 값 |
|----------|
| 우수 |
| 보통 |
| 보완 필요 |

---

#### needs_improvement

| 필드 | 타입 | 설명 |
|----------|----------|----------|
| weak_keywords | array | 보완 필요 키워드 |
| items | object | 보완 필요 항목 |

---

## 3. 추천활동 생성

### POST /resume/analyze/activities

이력서 분석 결과와 채용공고 정보를 기반으로 취업 경쟁력 향상에 도움이 되는 추천활동 3개를 생성한다.

### 사용 데이터

| 데이터 | 설명 |
|----------|----------|
| evaluation_result.json | 5개 평가영역 평가 결과 |
| needs_improvement.json | 보완 필요 키워드 및 항목 |
| activity_recommendations.json | 추천활동 3개 전체 결과 |
| activity_1.json | 추천활동 1 |
| activity_2.json | 추천활동 2 |
| activity_3.json | 추천활동 3 |

### Response (전체 추천활동)

```json
{
  "recommended_activities": [
    {
      "title": "AWS Certified Data Engineer - Associate 취득",
      "description": "...",
      "category": "자격증"
    },
    {
      "title": "dbt + Airflow 기반 ELT 파이프라인 프로젝트",
      "description": "...",
      "category": "프로젝트"
    },
    {
      "title": "Kafka 실시간 파이프라인 경험 포트폴리오화",
      "description": "...",
      "category": "포트폴리오 개선"
    }
  ],
  "status": "success"
}
```

### Response (개별 추천활동)

```json
{
  "status": "success",
  "activity_index": 1,
  "activity": {
    "title": "AWS Certified Data Engineer - Associate 취득",
    "description": "...",
    "category": "자격증"
  }
}
```

### 응답 필드

#### recommended_activities

| 필드 | 타입 | 설명 |
|----------|----------|----------|
| recommended_activities | array | 추천활동 3개 |
| status | string | 생성 성공 여부 |

---

#### activity

| 필드 | 타입 | 설명 |
|----------|----------|----------|
| title | string | 추천활동 제목 |
| description | string | 추천활동 설명 |
| category | string | 추천활동 유형 |

---

#### category 값

| 값 |
|----------|
| 자격증 |
| 프로젝트 |
| 실습 |
| 포트폴리오 개선 |
| 학습 |

---

## 4. 생성 파일

| 파일명 | 설명 |
|----------|----------|
| evidence.json | 근거 추출 결과 |
| evaluation_result.json | 5개 평가영역 평가 결과 |
| needs_improvement.json | 보완 필요 항목 |
| feedback_detail.json | AI 종합 분석 및 영역별 피드백 |
| activity_recommendations.json | 추천활동 3개 전체 저장 |
| activity_1.json | 추천활동 1 |
| activity_2.json | 추천활동 2 |
| activity_3.json | 추천활동 3 |

---

## 5. 현재 미확정 사항

| 항목 | 현재 상태 |
|----------|----------|
| Request Body | Spring ↔ FastAPI 연동 방식 확정 후 작성 |
| user_id / resume_id / job_id | 현재 AI 코드에서 직접 사용하지 않음 |
| 점수 / 레이더 차트 | 별도 분석 모듈에서 처리 |
| 추천활동 icon | 프론트 또는 백엔드에서 category 기준 매핑 |
| 최종 프론트 전송용 JSON 정리 | 필요 시 별도 후처리 |
| 직무 카테고리 트렌드 반영 | 추후 category_trend 데이터 적용 예정 |
