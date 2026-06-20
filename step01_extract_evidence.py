# step01_extract_evidence.py
# 1단계: 통합 이력서 분석 파일과 선택된 회사 공고 1개를 정리해 평가 근거 생성
# 입력:
# - test.extracted_y.json
# - job/dummy_jobs_data_20260419_155200.json 안의 특정 공고 1개
#
# 실제 백엔드 연결 시:
# - resume_data: 사용자의 통합 이력서 분석 JSON
# - selected_job_data: 사용자가 선택한 채용공고 JSON 1개
# - job_file_meta: 공고 파일의 category, site, trend_summary 같은 상위 정보
#
# 처리:
# - 개인정보는 평가 근거에서 제외한다.
# - 선택된 공고의 요구기술, 주요업무, 자격요건, 우대사항을 정리한다.
# - 이력서의 기술스택, 프로젝트, 성과, 핵심 키워드를 정리한다.
# - 공고와 이력서에서 문자열상 겹치는 키워드만 matched_keywords로 참고 제공한다.
# - 부족한 키워드 판단은 하지 않는다. 부족 판단은 2단계 Sonnet이 수행한다.
# - 문제/해결/성과 판단은 코드가 하지 않고, 프로젝트 원문을 2단계 Sonnet이 해석할 수 있게 전달한다.
#
# 출력:
# - output/evidence.json

from pathlib import Path
import json
import re


BASE_DIR = Path(__file__).resolve().parent

RESUME_FILE = BASE_DIR / "test.extracted_y.json"
JOB_FILE = BASE_DIR / "job" / "dummy_jobs_data_20260419_155200.json"

# 테스트용: 공고 파일 안 jobs 배열에서 몇 번째 공고를 쓸지 선택
TARGET_JOB_INDEX = 0

OUTPUT_FILE = BASE_DIR / "output" / "evidence.json"


# 평가 항목 key 설명
# selected_job: 사용자가 선택한 채용공고 정보
# job_fit: 직무 적합도 / JD, NCS 기반 직무 연관성
# experience_specificity: 경험·성과 구체성 / STAR 기반 역할·행동·결과·수치
# technical_competency: 실무·기술 역량 / 기술 활용·구현·문제 해결
# document_quality: 문서 완성도 / ATS, 이력서 첨삭 관점의 가독성·구조·핵심 전달
# consistency_uniqueness: 경험 일관성·차별성 / 경험 연결성과 본인만의 강점


PERSONAL_KEYS = {
    "인적사항",
    "이름",
    "이메일",
    "전화번호",
    "주소",
    "위치",
    "생년월일"
}


TECH_ALIASES = {
    "springboot": ["springboot", "spring boot", "스프링부트", "spring"],
    "javascript": ["javascript", "js", "자바스크립트"],
    "typescript": ["typescript", "ts", "타입스크립트"],
    "python": ["python", "파이썬"],
    "java": ["java", "자바"],
    "postgresql": ["postgresql", "postgres", "postgre"],
    "mysql": ["mysql", "my sql"],
    "sql": ["sql", "db", "database", "데이터베이스", "rdbms"],
    "aws": ["aws", "ec2", "s3", "rds", "redshift", "cloud"],
    "docker": ["docker", "도커"],
    "linux": ["linux", "리눅스"],
    "kafka": ["kafka", "apache kafka", "카프카"],
    "spark": ["spark", "apache spark", "spark sql", "스파크"],
    "airflow": ["airflow", "에어플로우"],
    "react": ["react", "리액트"],
    "django": ["django", "장고"],
    "flask": ["flask", "플라스크"],
    "api": ["api", "rest api", "restful api", "rest"],
    "llm": ["llm", "large language model", "언어모델"],
    "rag": ["rag", "graphrag", "graph rag"],
    "etl": ["etl", "elt", "데이터 파이프라인", "파이프라인"]
}


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data, file_path):
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def clean_text(value):
    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    return str(value).strip()


def unique_list(items, limit=50):
    result = []

    for item in items:
        item = clean_text(item)

        if item and item not in result:
            result.append(item)

    return result[:limit]


def flatten_text(value, parent_key=""):
    texts = []

    if parent_key in PERSONAL_KEYS:
        return texts

    if isinstance(value, dict):
        for key, val in value.items():
            if key in PERSONAL_KEYS:
                continue
            texts.extend(flatten_text(val, key))

    elif isinstance(value, list):
        for item in value:
            texts.extend(flatten_text(item, parent_key))

    elif isinstance(value, str):
        if value.strip():
            texts.append(value.strip())

    elif value is not None:
        texts.append(str(value))

    return texts


def normalize(text):
    text = clean_text(text).lower()
    text = re.sub(r"[\s\-_./]", "", text)
    return text


def keyword_in_text(keyword, text):
    keyword_norm = normalize(keyword)
    text_norm = normalize(text)

    if not keyword_norm:
        return False

    if keyword_norm in text_norm:
        return True

    for alias_key, aliases in TECH_ALIASES.items():
        normalized_aliases = [normalize(alias) for alias in aliases]

        if keyword_norm == normalize(alias_key) or keyword_norm in normalized_aliases:
            return any(alias in text_norm for alias in normalized_aliases)

    return False


def extract_number_phrases(texts):
    patterns = [
        r"[^.。\n]*\d+%[^.。\n]*",
        r"[^.。\n]*\d+명[^.。\n]*",
        r"[^.。\n]*\d+개[^.。\n]*",
        r"[^.。\n]*\d+초[^.。\n]*",
        r"[^.。\n]*\d+분[^.。\n]*",
        r"[^.。\n]*\d+시간[^.。\n]*",
        r"[^.。\n]*\d+건[^.。\n]*",
        r"[^.。\n]*\d+회[^.。\n]*",
        r"[^.。\n]*\d+배[^.。\n]*",
        r"[^.。\n]*\d+년[^.。\n]*",
        r"[^.。\n]*\d+개월[^.。\n]*",
        r"[^.。\n]*\d+만\s*건[^.。\n]*"
    ]

    result = []

    for text in texts:
        text = clean_text(text)

        if not text:
            continue

        for pattern in patterns:
            matches = re.findall(pattern, text)

            for match in matches:
                match = match.strip()

                if match and match not in result:
                    result.append(match)

    return result[:30]


def select_job_from_file(job_file_data, target_index=0):
    jobs = job_file_data.get("jobs", [])

    if not isinstance(jobs, list) or not jobs:
        raise ValueError("공고 파일에 jobs 배열이 없거나 비어 있습니다.")

    if target_index >= len(jobs):
        raise IndexError(f"TARGET_JOB_INDEX가 범위를 벗어났습니다. jobs 개수: {len(jobs)}")

    return jobs[target_index]


def summarize_selected_job(job_file_data, selected_job):
    detail = selected_job.get("detail", {})
    position = selected_job.get("position", {})
    company = selected_job.get("company", {})

    return {
        "site": job_file_data.get("site"),
        "category": job_file_data.get("category"),
        "job_id": selected_job.get("job_id"),
        "company_name": company.get("name"),
        "job_title": position.get("title") or selected_job.get("title"),
        "skills": selected_job.get("skills", []),
        "main_tasks": detail.get("main_tasks", []),
        "requirements": detail.get("requirements", []),
        "preferred": detail.get("preferred", []),
        "talent": detail.get("talent", []),
        "apply_document": selected_job.get("apply", {}).get("document", []),
        "recruitment_process": selected_job.get("recruitment_process", {}),
        "trend_summary": job_file_data.get("trend_summary", {})
    }


def get_job_keywords(job_summary):
    keywords = []

    keywords.append(job_summary.get("category"))
    keywords.append(job_summary.get("job_title"))
    keywords.extend(job_summary.get("skills", []))

    trend = job_summary.get("trend_summary", {})
    keywords.extend(trend.get("hot_frameworks", []))
    keywords.extend(trend.get("hot_languages", []))
    keywords.extend(trend.get("hot_tools", []))
    keywords.extend(trend.get("talent_keywords", []))

    return unique_list(keywords, limit=80)


def get_resume_tech(resume):
    tech = []

    stack = resume.get("기술_스택", {})

    if isinstance(stack, dict):
        for value in stack.values():
            if isinstance(value, list):
                tech.extend(value)

    for project in resume.get("프로젝트", []):
        if isinstance(project, dict):
            tech.extend(project.get("기술스택", []))

    return unique_list(tech, limit=100)


def get_project_names(resume):
    names = []

    for project in resume.get("프로젝트", []):
        if isinstance(project, dict):
            names.append(project.get("이름"))

    return unique_list(names, limit=30)


def get_project_evidence(resume):
    projects = []

    for project in resume.get("프로젝트", []):
        if not isinstance(project, dict):
            continue

        project_texts = [
            project.get("이름"),
            project.get("기간"),
            project.get("역할"),
            project.get("설명")
        ]

        project_texts.extend(project.get("성과_수치", []))

        projects.append({
            "name": clean_text(project.get("이름")),
            "period": clean_text(project.get("기간")),
            "role": clean_text(project.get("역할")),
            "tech_stack": project.get("기술스택", []),
            "description": clean_text(project.get("설명")),
            "results": project.get("성과_수치", []),
            "number_evidence": extract_number_phrases(project_texts)
        })

    return projects[:10]


def find_matched_job_keywords(job_keywords, resume_texts):
    joined_text = " ".join(resume_texts)
    matched = []

    for keyword in job_keywords:
        if keyword_in_text(keyword, joined_text):
            matched.append(keyword)

    return unique_list(matched, limit=40)


def analyze_document_quality(resume):
    projects = get_project_evidence(resume)

    project_count = len(projects)
    projects_with_role = 0
    projects_with_description = 0
    projects_with_results = 0
    projects_with_numbers = 0

    for project in projects:
        if project.get("role"):
            projects_with_role += 1

        if project.get("description"):
            projects_with_description += 1

        if project.get("results"):
            projects_with_results += 1

        if project.get("number_evidence"):
            projects_with_numbers += 1

    return {
        "project_count": project_count,
        "projects_with_role": projects_with_role,
        "projects_with_description": projects_with_description,
        "projects_with_results": projects_with_results,
        "projects_with_numbers": projects_with_numbers,
        "has_core_keywords": bool(resume.get("핵심_키워드")),
        "has_tech_stack": bool(get_resume_tech(resume)),
        "has_awards_or_certificates": bool(resume.get("자격증_수상")),
        "has_extra_activities": bool(resume.get("활동_기타"))
    }


def build_evidence(job_summary, resume):
    job_keywords = get_job_keywords(job_summary)
    resume_texts = flatten_text(resume)

    matched_keywords = find_matched_job_keywords(
        job_keywords=job_keywords,
        resume_texts=resume_texts
    )

    applicant_tech = get_resume_tech(resume)
    project_evidence = get_project_evidence(resume)

    core_keywords = resume.get("핵심_키워드", [])
    keyword_frequency = resume.get("전체_키워드_빈도", {})

    repeated_strengths = []

    if isinstance(keyword_frequency, dict):
        for key, value in keyword_frequency.items():
            if isinstance(value, int) and value >= 2:
                repeated_strengths.append(key)

    evidence = {
        "selected_job": {
            "site": job_summary.get("site"),
            "category": job_summary.get("category"),
            "job_id": job_summary.get("job_id"),
            "company_name": job_summary.get("company_name"),
            "job_title": job_summary.get("job_title")
        },

        "job_fit": {
            "criterion": "직무 적합도",
            "meaning": "JD/NCS 기반 직무 연관성",
            "reference_basis": "NCS 직무기술서 + 고용24 채용공고",
            "job_title": job_summary.get("job_title"),
            "company_name": job_summary.get("company_name"),
            "job_required_skills": job_summary.get("skills", []),
            "job_main_tasks": job_summary.get("main_tasks", []),
            "job_requirements": job_summary.get("requirements", []),
            "job_preferred": job_summary.get("preferred", []),
            "job_talent": job_summary.get("talent", []),
            "matched_keywords": matched_keywords,
            "applicant_tech": applicant_tech,
            "applicant_core_keywords": core_keywords,
            "project_evidence": project_evidence
        },

        "experience_specificity": {
            "criterion": "경험·성과 구체성",
            "meaning": "역할·행동·결과·수치",
            "reference_basis": "STAR 경험 평가 방식",
            "project_evidence": project_evidence
        },

        "technical_competency": {
            "criterion": "실무·기술 역량",
            "meaning": "기술 활용·구현·문제 해결",
            "reference_basis": "NCS 직무 수행 역량 + 개발자 포트폴리오 평가 관점",
            "used_technologies": applicant_tech,
            "project_evidence": project_evidence
        },

        "document_quality": {
            "criterion": "문서 완성도",
            "meaning": "가독성·구조·핵심 전달",
            "reference_basis": "ATS/이력서 첨삭 관점",
            "document_quality_signals": analyze_document_quality(resume)
        },

        "consistency_uniqueness": {
            "criterion": "경험 일관성·차별성",
            "meaning": "경험 연결성·본인만의 강점",
            "reference_basis": "자기소개서 첨삭 및 직무 방향성 평가 관점",
            "core_keywords": core_keywords,
            "keyword_frequency": keyword_frequency,
            "repeated_strength_keywords": repeated_strengths,
            "project_names": get_project_names(resume),
            "awards_certificates": resume.get("자격증_수상", []),
            "extra_activities": resume.get("활동_기타", []),
            "project_evidence": project_evidence
        }
    }

    return evidence


def validate_inputs(resume, job_summary):
    warnings = []

    if not resume.get("프로젝트"):
        warnings.append("이력서 분석 파일에 프로젝트 정보가 없습니다.")

    if not get_resume_tech(resume):
        warnings.append("이력서 분석 파일에 기술스택 정보가 없습니다.")

    if not job_summary.get("skills") and not job_summary.get("main_tasks") and not job_summary.get("requirements"):
        warnings.append("선택된 공고에서 요구기술, 주요업무, 자격요건을 충분히 찾지 못했습니다.")

    return warnings


def run_step01(resume_data, selected_job_data, job_file_meta=None):
    """
    실제 백엔드 연결 시 사용할 함수.
    resume_data: 통합 이력서 분석 JSON
    selected_job_data: 사용자가 선택한 채용공고 JSON 1개
    job_file_meta: category, site, trend_summary 같은 상위 공고 파일 정보
    """

    if job_file_meta is None:
        job_file_meta = {}

    job_file_data = {
        "site": job_file_meta.get("site"),
        "category": job_file_meta.get("category"),
        "trend_summary": job_file_meta.get("trend_summary", {})
    }

    job_summary = summarize_selected_job(job_file_data, selected_job_data)
    evidence = build_evidence(job_summary, resume_data)

    return evidence


def main():
    resume = load_json(RESUME_FILE)
    job_file_data = load_json(JOB_FILE)

    selected_job = select_job_from_file(
        job_file_data=job_file_data,
        target_index=TARGET_JOB_INDEX
    )

    job_summary = summarize_selected_job(
        job_file_data=job_file_data,
        selected_job=selected_job
    )

    print("=== 선택된 공고 ===")
    print(f"카테고리: {job_summary.get('category')}")
    print(f"회사: {job_summary.get('company_name')}")
    print(f"공고명: {job_summary.get('job_title')}")
    print(f"공고 ID: {job_summary.get('job_id')}")

    warnings = validate_inputs(resume, job_summary)

    if warnings:
        print("\n=== 1단계 입력 데이터 경고 ===")
        for warning in warnings:
            print(f"- {warning}")

    evidence = build_evidence(job_summary, resume)

    save_json(evidence, OUTPUT_FILE)

    print("\n=== 1단계 근거 추출 완료 ===")
    print(json.dumps(evidence, ensure_ascii=False, indent=2))
    print(f"\n저장 완료: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()