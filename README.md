# Resume Feedback AI Server

이력서, 자기소개서, 포트폴리오와 채용공고를 기반으로 AI 피드백 및 추천활동을 생성하는 모듈입니다.

---

## 프로젝트 구성

### AI 피드백 분석

사용자의 이력서, 자기소개서, 포트폴리오와 선택한 채용공고를 기반으로 다음 정보를 생성합니다.

- AI 종합 분석
- 5개 평가영역별 피드백
- 보완 필요 키워드
- 보완 필요 영역

### 추천활동 생성

이력서 분석 결과를 기반으로 취업 경쟁력 향상에 도움이 되는 추천활동 3개를 생성합니다.

- 자격증
- 프로젝트
- 실습
- 포트폴리오 개선
- 학습

---

## API 문서

상세 API 명세는 `api.md` 참고

### Endpoint

```text
POST /resume/analyze/feedback

POST /resume/analyze/activities
```

---

## 필요 라이브러리

requirements.txt 사용

```bash
pip install -r requirements.txt
```

또는

```bash
pip install fastapi uvicorn pydantic anthropic python-dotenv
```

---

## 환경변수

Claude API 사용을 위해 아래 환경변수 설정이 필요합니다.

```env
ANTHROPIC_API_KEY=YOUR_API_KEY
CLAUDE_MODEL_NAME=claude-sonnet-4-6
```

현재 코드는 환경변수 기반으로 작성되어 있으며 실제 API 키는 포함되어 있지 않습니다.

---

## 실행 구조

### step01_extract_evidence.py

이력서와 채용공고를 비교하여 근거 데이터를 추출

생성 파일

```text
evidence.json
```

---

### step02_evaluate_level.py

5개 평가영역 평가 수행

생성 파일

```text
evaluation_result.json
needs_improvement.json
```

---

### step03_1_generate_feedback.py

AI 종합 분석 및 영역별 피드백 생성

생성 파일

```text
feedback_detail.json
```

---

### step03_2_generate_activities.py

추천활동 3개 생성

생성 파일

```text
activity_recommendations.json
activity_1.json
activity_2.json
activity_3.json
```

---

## 생성 파일

```text
evidence.json

evaluation_result.json

needs_improvement.json

feedback_detail.json

activity_recommendations.json

activity_1.json
activity_2.json
activity_3.json
```

---

## 참고 사항

- Request Body는 Spring ↔ FastAPI 연동 방식 확정 후 정의 예정
- Claude API Key는 GitHub에 포함되어 있지 않음
- 실제 운영 시 서버 환경변수 설정 필요
- 테스트용 이력서 데이터(`test.extracted_y.json`)는 개인정보 보호를 위해 GitHub에 포함하지 않음
- 점수 및 레이더 차트는 별도 모듈에서 처리
